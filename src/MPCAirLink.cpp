// VBAN UDP -> PCM float -> rate conversion -> SPSC -> prebuffer -> gain -> stereo.
#include "mpc_plugin.h"
#include "Receiver.h"
#include <mutex>
#include <cstdio>
#include <pthread.h>
#include <sched.h>

enum { Reserved, ReceiveMode, Latency, Gain, Address, Connection, StreamName, Format, Lost, MeterL, MeterR, Overflows, Underruns, AirPlayStatus, SourceMode, MeterRefresh, BufferTexture, OutputTexture };
class MPCAirLink final : public mpc::Plugin {
    airlink::Receiver receiver;
    airlink::Renderer renderer;
    std::mutex statusMutex; // Only worker and text formatting; never accessed by process().
    airlink::Status status;
    std::mutex latestMutex;
    airlink::Status latestStatus;
    std::atomic<bool> displayRunning{true};
    std::thread displayThread;
    std::array<std::string,5> text{};
    std::string airplayText;
    uint32_t seenEpoch=0;int publishedSource=-1;
    float meterEnvelopeL=0,meterEnvelopeR=0;
    float lastTextureValue=-1; // Display worker only; only Output is animated.
    float sampleRate=44100;
    std::atomic<uint32_t> hostResets{0};
    static mpc::PluginInfo identity() {
        mpc::PluginInfo i; i.name="MPC AirLink"; i.vendor="sttm";
        i.uniqueId=MPC_FOURCC('A','r','L','k'); i.version=1300;
        i.isInstrument=true; i.numInputs=0; i.numOutputs=2; return i;
    }
    void update(const airlink::Status& s) {
        char fmt[64];
        if(s.rate) std::snprintf(fmt,sizeof fmt,"%.4g kHz / %s %s",s.rate/1000.,s.format==1?"16-bit":s.format==2?"24-bit":"Float32",s.channels==1?"Mono":"Stereo");
        else std::snprintf(fmt,sizeof fmt,"--");
        std::array<std::string,5> next{{s.ip+" : 6980",s.error?"SOCKET ERROR "+std::to_string(s.error):s.receiving?"RECEIVING":"WAITING",s.name,fmt,"Lost: "+std::to_string(s.lost)}};
        std::array<bool,5> changed{};
        std::string ap=receiver.mode.load()==1?"AirPlay disabled":s.airplayReady?"AirPlay: MPC AirLink":s.airplayError?"AirPlay error "+std::to_string(s.airplayError):"AirPlay starting";
        if(receiver.mode.load()==1) {
            if(!s.receiving) ap="VBAN ready / UDP 6980";
            else {
                int host=std::max(8000,receiver.hostRate.load());
                unsigned depth=unsigned(uint64_t(receiver.ring.size())*1000/unsigned(host));
                depth=((depth+5)/10)*10;
                char diagnostic[64];std::snprintf(diagnostic,sizeof diagnostic,"VBAN / BUFFER %u ms / RESETS %u",depth,hostResets.load());ap=diagnostic;
            }
        }
        bool apChanged=false;
        {
            std::lock_guard<std::mutex> lock(statusMutex);
            status=s; apChanged=airplayText!=ap; airplayText=ap;
            for(size_t n=0;n<5;++n) { changed[n]=text[n]!=next[n]; text[n]=next[n]; }
        }
        int source=getInt(SourceMode);if(source!=publishedSource){publishedSource=source;notifyHostParameterChanged(SourceMode);}
        // Toggle a readout token only when its text changes. Host notification is worker-only.
        for(int n=0;n<5;++n) if(changed[n]) { set(Address+n,1-get(Address+n)); notifyHostParameterChanged(Address+n); }
        if(apChanged) {set(AirPlayStatus,1-get(AirPlayStatus)); notifyHostParameterChanged(AirPlayStatus);}
        auto publish=[&](int index,float value) {
            if(getNormalised(index)!=param(index).toNormalised(value)) {set(index,value); notifyHostParameterChanged(index);}
        };
        publish(Overflows,float(s.overflows)+float(renderer.discarded.load())); publish(Underruns,float(renderer.underruns.load()));
    }
    void updateTextures() {
        float value=getNormalised(Gain);
        if(value==lastTextureValue)return;
        lastTextureValue=value;
        // Two center images, one change per five degrees. Preserve the
        // shipped 0..5 auxiliary parameter ranges; use their endpoints.
        float next=(int(std::clamp(value,0.f,1.f)*54)%2)?5.f:0.f;
        if(get(OutputTexture)!=next){set(OutputTexture,next);notifyHostParameterChanged(OutputTexture);}
    }
    void updateMeters(double elapsed) {
#ifdef AIRLINK_METER_FRAME_HOOK
        AIRLINK_METER_FRAME_HOOK();
#endif
        float release=float(std::exp(-std::max(0.,elapsed)/.120));
        meterEnvelopeL=std::max(renderer.peakL.exchange(0),meterEnvelopeL*release);
        meterEnvelopeR=std::max(renderer.peakR.exchange(0),meterEnvelopeR*release);
        const int indices[]={MeterL,MeterR};const float envelopes[]={meterEnvelopeL,meterEnvelopeR};
        for(int k=0;k<2;++k){
            float value=std::round(std::clamp(envelopes[k],0.f,1.f)*22)/22;
            if(getNormalised(indices[k])!=value){set(indices[k],value);notifyHostParameterChanged(indices[k]);}
        }
    }
public:
    MPCAirLink() : mpc::Plugin(identity()) {
        // Parameter zero is intentionally inert: MPC nudges it when loading an instrument.
        auto inert=mpc::floatParam("host_reserved","Host",0,1,0); inert.automatable=false; addParam(inert);
        addParam(mpc::choiceParam("receive_mode","Receive Mode",{"AirPlay","VBAN Only","AirPlay Only"},2));
        addParam(mpc::intParam("latency","Jitter Buffer",10,150,120,"ms"));
        addParam(mpc::floatParam("gain","Output Gain",-24,12,0,"dB",1));
        const char* ids[]={"address","connection","stream_name","stream_format","lost","meter_l","meter_r","overflows","underruns"};
        const char* names[]={"MPC IP / UDP","Status","Active Stream","Audio Format","Lost Packets","Level L","Level R","Overflows","Underruns"};
        for(int n=0;n<9;++n) { auto p=mpc::floatParam(ids[n],names[n],0,n>=7?16777215.f:1.f,0); p.automatable=false; addParam(p); }
        auto ap=mpc::floatParam("airplay_status","AirPlay",0,1,0); ap.automatable=false; addParam(ap);
        addParam(mpc::choiceParam("source_mode","Source",{"AirPlay","VBAN"},0));
        auto refresh=mpc::choiceParam("meter_refresh","Meter Refresh",{"10 Hz","24 Hz"},1);refresh.automatable=false;addParam(refresh); // Legacy state only; fixed 24 Hz.
        // Keep shipped IDs, ranges and defaults. These cosmetic readouts now
        // Output selects two center textures; Buffer phase is now inert.
        auto bt=mpc::intParam("buffer_texture_phase","Buffer Texture",0,5,3);bt.automatable=false;addParam(bt);
        auto ot=mpc::intParam("output_texture_phase","Output Texture",0,5,0);ot.automatable=false;addParam(ot);
        receiver.contentDirectory=mpc::detail::computePluginFolder()+"/Content";
        receiver.onStatus=[this](const airlink::Status& s){std::lock_guard<std::mutex> lock(latestMutex); latestStatus=s;};
        receiver.mode.store(getInt(ReceiveMode)==1?1:2);receiver.latencyMs.store(int(get(Latency)));
        receiver.start();
        // MPC host callbacks may be slow: never stop draining AirPlay/UDP to update a meter.
        displayThread=std::thread([this] {
            sched_param normal{};(void)pthread_setschedparam(pthread_self(),SCHED_OTHER,&normal);
            using Clock=std::chrono::steady_clock;
            auto nextStatus=Clock::now(),nextMeter=nextStatus,lastMeter=nextStatus;
            while(displayRunning.load(std::memory_order_acquire)) {
                auto now=Clock::now();
                if(now>=nextStatus){
                    airlink::Status snapshot;
                    {std::lock_guard<std::mutex> lock(latestMutex);snapshot=latestStatus;}
                    update(snapshot);nextStatus=Clock::now()+std::chrono::milliseconds(100);
                }
                now=Clock::now();
                if(now>=nextMeter){
                    updateTextures();
                    updateMeters(std::chrono::duration<double>(now-lastMeter).count());lastMeter=now;
                    auto period=std::chrono::nanoseconds(41666667); // Fixed 24 Hz; legacy saved values are ignored.
                    nextMeter+=period;auto after=Clock::now();if(nextMeter<=after)nextMeter=after+period;
                }
                std::this_thread::sleep_until(std::min(nextStatus,nextMeter));
            }
        });
    }
    ~MPCAirLink() override { displayRunning.store(false,std::memory_order_release); if(displayThread.joinable()) displayThread.join(); receiver.stop(); }
    void prepare(double rate,int) override { sampleRate=float(std::clamp(rate,8000.,192000.)); receiver.hostRate.store(int(sampleRate)); }
    void reset() override {
        hostResets.fetch_add(1,std::memory_order_relaxed);
        // A network instrument has no note voices to reset. Re-preparing the host
        // must not interrupt an already active VBAN stream or erase its prebuffer.
        if(receiver.activeSource.load(std::memory_order_acquire)==1) return;
        receiver.ring.discard(); renderer.reset();
    }
    void parameterChanged(int index,float value) override {
        static thread_local bool syncing=false;if(syncing)return;
        if(index==ReceiveMode){int source=int(std::lround(value))==1?1:0;receiver.mode.store(source?1:2);syncing=true;if(getInt(SourceMode)!=source)set(SourceMode,float(source));syncing=false;}
        if(index==SourceMode){int source=int(std::lround(value));receiver.mode.store(source?1:2);syncing=true;if((getInt(ReceiveMode)==1?1:0)!=source)set(ReceiveMode,source?1.f:2.f);syncing=false;}
        if(index==Latency)receiver.latencyMs.store(std::clamp(int(std::lround(value)),10,150));

    }
    void process(mpc::ProcessContext& ctx) override {
        auto epoch=receiver.epoch.load(std::memory_order_acquire);
        if(epoch!=seenEpoch) { receiver.ring.discard(); renderer.rebuffer(); seenEpoch=epoch; }
        if(ctx.numOutputs<2) return;
        float latency=float(airlink::playbackBufferMs(receiver.activeSource.load(std::memory_order_acquire),getInt(Latency)));
        renderer.render(receiver.ring,ctx.outputs[0],ctx.outputs[1],ctx.numFrames,int(latency*sampleRate/1000),std::pow(10.f,get(Gain)/20),true,int(sampleRate));
    }
    bool formatValue(int index,float value,std::string& out) override {
        if(index==Latency || index==Gain || index==Overflows || index==Underruns) {
            char b[64]; if(index==Latency) std::snprintf(b,sizeof b,"%.0f ms",double(value));
            else if(index==Gain) std::snprintf(b,sizeof b,"%.1f dB",double(value));
            else std::snprintf(b,sizeof b,"%s: %.0f",index==Overflows?"Drop":"XRUN",double(value));
            out=b; return true;
        }
        if(index==AirPlayStatus) { std::lock_guard<std::mutex> lock(statusMutex); out=airplayText; return true; }
        if(index>=Address && index<=Lost) { std::lock_guard<std::mutex> lock(statusMutex); out=text[size_t(index-Address)]; return true; }
        return false;
    }
};
MPC_PLUGIN_ENTRY(MPCAirLink)
