#pragma once
#include <array>
#include <atomic>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>

namespace airlink {
static_assert(std::atomic<uint32_t>::is_always_lock_free, "SPSC requires lock-free 32-bit atomics");
static_assert(std::atomic<float>::is_always_lock_free, "Meters require lock-free floats");
struct Stereo { float l=0, r=0; };
template<uint32_t N> class Ring {
    static_assert((N & (N-1)) == 0, "power of two");
    std::array<Stereo,N> data{};
    alignas(64) std::atomic<uint32_t> w{0};
    alignas(64) std::atomic<uint32_t> r{0};
public:
    bool push(Stereo s) {
        auto a=w.load(std::memory_order_relaxed);
        if (a-r.load(std::memory_order_acquire)==N) return false;
        data[a&(N-1)]=s; w.store(a+1,std::memory_order_release); return true;
    }
    uint32_t pushMany(const Stereo* samples,uint32_t count) {
        auto head=w.load(std::memory_order_relaxed);
        auto tail=r.load(std::memory_order_acquire);
        uint32_t amount=std::min(count,N-(head-tail));
        uint32_t first=std::min(amount,N-(head&(N-1)));
        std::copy_n(samples,first,data.begin()+(head&(N-1)));
        std::copy_n(samples+first,amount-first,data.begin());
        w.store(head+amount,std::memory_order_release);
        return amount;
    }
    bool pop(Stereo& s) {
        auto a=r.load(std::memory_order_relaxed);
        if(a==w.load(std::memory_order_acquire)) return false;
        s=data[a&(N-1)]; r.store(a+1,std::memory_order_release); return true;
    }
    uint32_t size() const {
        // Reading tail first also makes this a bounded snapshot for the non-RT UI.
        auto tail=r.load(std::memory_order_acquire);
        auto head=w.load(std::memory_order_acquire);
        return std::min(N,head-tail);
    }
    // Consumer only: never reset the producer's write cursor.
    void trim(uint32_t target) {
        auto end=w.load(std::memory_order_acquire);
        if(end-r.load(std::memory_order_relaxed)>target) r.store(end-target,std::memory_order_release);
    }
    void discard() { r.store(w.load(std::memory_order_acquire),std::memory_order_release); }
};
inline uint32_t le32(const uint8_t* p) { return uint32_t(p[0])|uint32_t(p[1])<<8|uint32_t(p[2])<<16|uint32_t(p[3])<<24; }
struct Packet {
    static constexpr int rates[21]={6000,12000,24000,48000,96000,192000,384000,8000,16000,32000,64000,128000,256000,512000,11025,22050,44100,88200,176400,352800,705600};
    int rate=0, frames=0, channels=0, format=0, bytes=0;
    uint32_t sequence=0;
    std::array<char,17> name{};
    const uint8_t* audio=nullptr;
    bool parse(const uint8_t* p,size_t n) {
        if(n<28 || std::memcmp(p,"VBAN",4) || (p[4]&0xe0) || (p[4]&31)>20 || (p[7]&0xf8)) return false;
        format=p[7]&7; bytes=format==1?2:format==2?3:format==4?4:0;
        frames=int(p[5])+1; channels=int(p[6])+1;
        if(!bytes || channels>2 || n!=28+size_t(frames*channels*bytes)) return false;
        rate=rates[p[4]&31]; sequence=le32(p+24); name.fill(0);
        for(int i=0;i<16 && p[8+i];++i) { if(p[8+i]<32 || p[8+i]>126) return false; name[i]=char(p[8+i]); }
        audio=p+28; return true;
    }
    float sample(int f,int ch) const {
        auto p=audio+(f*channels+ch)*bytes;
        if(format==1) { int32_t x=int32_t(p[0])+(int32_t(p[1])<<8); if(x&0x8000) x-=65536; return float(x)/32768.f; }
        if(format==2) { int32_t x=int32_t(p[0])+(int32_t(p[1])<<8)+(int32_t(p[2])<<16); if(x&0x800000) x-=16777216; return float(x)/8388608.f; }
        uint32_t bits=le32(p); float x; std::memcpy(&x,&bits,4);
        return std::isfinite(x)?std::clamp(x,-1.f,1.f):0.f;
    }
};
// Persistent interpolation state spans packet boundaries. Output rate may change at prepare().
class Resampler {
    Stereo previous{};
    double next=0;
    bool have=false;
public:
    void reset() { have=false; next=0; }
    template<class Emit> void feed(Stereo s,double ratio,Emit emit) {
        if(!have) { previous=s; have=true; emit(s); next=ratio; return; }
        while(next<=1.0) { float t=float(next); emit({previous.l+(s.l-previous.l)*t,previous.r+(s.r-previous.r)*t}); next+=ratio; }
        next-=1; previous=s;
    }
};
class Renderer {
    bool playing=false;
    float fade=0, gain=1;
    Stereo last{}, transition{};
    int lastThreshold=-1;
    bool primed=false;
    Stereo a{},b{};
    double phase=0, filteredFill=0, clockRatio=1;
    template<uint32_t N> bool take(Ring<N>& ring,Stereo& out,bool adaptive) {
        if(!adaptive) return ring.pop(out);
        if(!primed) { if(!ring.pop(a) || !ring.pop(b)) return false; phase=0; primed=true; }
        float t=float(phase); out={a.l+(b.l-a.l)*t,a.r+(b.r-a.r)*t};
        phase+=clockRatio;
        while(phase>=1) { phase-=1; a=b; if(!ring.pop(b)) {primed=false; return false;} }
        return true;
    }
public:
    std::atomic<float> peakL{0},peakR{0};
    std::atomic<uint32_t> underruns{0}, discarded{0};
    void reset() { playing=false; fade=0; last={}; transition={}; lastThreshold=-1; primed=false; phase=0; clockRatio=1; filteredFill=0; }
    void rebuffer() { playing=false; fade=0; primed=false; phase=0; clockRatio=1; }
    template<uint32_t N> void render(Ring<N>& ring,float* l,float* r,int frames,int threshold,float target,bool adaptive=false,int rate=44100) {
        float pl=0,pr=0;
        auto trim=[&] {
            auto before=ring.size(); ring.trim(uint32_t(threshold));
            if(before>uint32_t(threshold)) discarded.fetch_add(before-uint32_t(threshold),std::memory_order_relaxed);
            transition=last; fade=0; primed=false;
        };
        if(threshold!=lastThreshold) {
            if(lastThreshold>=0) {
                if(threshold>lastThreshold) playing=false;
                else trim();
            }
            lastThreshold=threshold;
        }
        if(!playing && ring.size()>=uint32_t(threshold)) { playing=true; fade=0; transition=last; primed=false; filteredFill=threshold; }
        // Consumer alone drops excess backlog after host suspension or a long stall.
        if(ring.size()>uint32_t(threshold+std::max(rate/2,8192))) trim();
        if(adaptive && playing) {
            // Slow FIFO feedback matches independent sender/DAC clocks. Filter out packet bursts.
            double dt=double(frames)/std::max(rate,8000);
            filteredFill+=std::min(1.0,dt)*(double(ring.size())-filteredFill);
            double wanted=1+std::clamp((filteredFill-threshold)/(std::max(rate,8000)*5.0),-0.003,0.003);
            clockRatio+=std::clamp(wanted-clockRatio,-dt*0.0015,dt*0.0015);
        }
        for(int i=0;i<frames;++i) {
            Stereo s{};
            if(playing && take(ring,s,adaptive)) { fade=std::min(1.f,fade+1.f/128); last={s.l*fade+transition.l*(1-fade),s.r*fade+transition.r*(1-fade)}; }
            else { if(playing) { playing=false; primed=false; underruns.fetch_add(1,std::memory_order_relaxed); } last.l*=0.97f; last.r*=0.97f; if(std::fabs(last.l)<1e-8f) last.l=0; if(std::fabs(last.r)<1e-8f) last.r=0; }
            gain+=0.002f*(target-gain);
            l[i]=last.l*gain; r[i]=last.r*gain; pl=std::max(pl,std::fabs(l[i])); pr=std::max(pr,std::fabs(r[i]));
        }
        // Accumulate block peaks until the UI samples them. Release uses elapsed time in the UI.
        peakL.store(std::max(pl,peakL.load())); peakR.store(std::max(pr,peakR.load()));
    }
};
}
