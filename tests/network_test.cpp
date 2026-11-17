#include "../src/MPCAirLink.cpp"
#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>
#include <cassert>
#include <chrono>
#include <iostream>
#include <vector>
using namespace std::chrono_literals;
int main() {
    MPCAirLink plugin; assert(plugin.getInt(SourceMode)==0&&plugin.getInt(ReceiveMode)==2);
    plugin.set(SourceMode,1);assert(plugin.getInt(ReceiveMode)==1);plugin.set(SourceMode,0);assert(plugin.getInt(ReceiveMode)==2);plugin.set(ReceiveMode,0);assert(plugin.getInt(SourceMode)==0);plugin.set(ReceiveMode,1); plugin.prepare(44100,512); plugin.set(Latency,40);
    assert(std::string(plugin.info().name)=="MPC AirLink");
    assert(plugin.info().uniqueId==MPC_FOURCC('A','r','L','k'));
    assert(plugin.numParams()==16 && plugin.param(1).id=="receive_mode");
    for(int i=0;i<plugin.numParams();++i) assert(plugin.param(i).id!="stream_filter");
    int sock=socket(AF_INET,SOCK_DGRAM,0); assert(sock>=0);
    sockaddr_in dest{}; dest.sin_family=AF_INET; dest.sin_port=htons(6980); inet_pton(AF_INET,"127.0.0.1",&dest.sin_addr);
    std::this_thread::sleep_for(100ms);
    auto send=[&](uint32_t seq,const char* name,int channels,int fmt,int sr,int frames=128) {
        std::vector<uint8_t> b(28+size_t(frames*channels*(fmt==1?2:fmt==2?3:4)),0);
        std::memcpy(b.data(),"VBAN",4); b[4]=uint8_t(sr); b[5]=uint8_t(frames-1); b[6]=uint8_t(channels-1); b[7]=uint8_t(fmt);
        std::memcpy(b.data()+8,name,std::strlen(name)); for(int k=0;k<4;++k) b[24+k]=uint8_t(seq>>(8*k));
        for(int i=0;i<frames;++i) for(int c=0;c<channels;++c) {
            double x=0.5*std::sin(2*3.141592653589793*1000*(double(seq)*128+i)/airlink::Packet::rates[sr]); if(c) x=-x;
            int step=fmt==1?2:fmt==2?3:4; uint32_t v;
            if(fmt==4) {float f=float(x); std::memcpy(&v,&f,4);} else v=uint32_t(int32_t(x*(fmt==1?32767:8388607)));
            for(int k=0;k<step;++k) b[28+(i*channels+c)*step+k]=uint8_t(v>>(8*k));
        }
        assert(sendto(sock,b.data(),b.size(),0,reinterpret_cast<sockaddr*>(&dest),sizeof dest)==ssize_t(b.size()));
    };
    auto waitText=[&](int index,const std::string& expected) {
        std::string value;
        for(int i=0;i<40;++i) {plugin.formatValue(index,0,value); if(value==expected) return; std::this_thread::sleep_for(20ms);}
        std::cerr<<"Expected text: "<<expected<<"; actual: "<<value<<std::endl;
        assert(false);
    };
    float l[512]{},r[512]{}; float* outputs[]={l,r}; mpc::ProcessContext ctx; ctx.outputs=outputs; ctx.numOutputs=2; ctx.numFrames=128;
    // Simulate real wall-clock host and sender, checking preserved 1 kHz pitch at 48 -> 44.1 kHz.
    std::atomic<bool> sending{true};
    std::thread sender([&]{ auto t=std::chrono::steady_clock::now(); uint32_t seq=0; while(sending.load()) {
        send(seq,"Stream1",2,1,3); ++seq; t+=std::chrono::nanoseconds(2666667); std::this_thread::sleep_until(t);
    }});
    double energy=0,stereoError=0; int crossings=0,measured=0; float previous=0;
    auto deadline=std::chrono::steady_clock::now();
    for(int block=0;block<200;++block) {
        if(block%7==0) plugin.reset(); // MPC re-prepare must preserve a live VBAN FIFO.
        plugin.process(ctx);
        if(block>30) for(int i=0;i<128;++i) { assert(std::isfinite(l[i])); energy+=l[i]*l[i]; stereoError+=std::fabs(l[i]+r[i]); if(previous<=0 && l[i]>0) ++crossings; previous=l[i]; ++measured; }
        deadline+=std::chrono::nanoseconds(2902494); std::this_thread::sleep_until(deadline);
    }
    sending.store(false); sender.join();
    double hz=double(crossings)*44100/measured;
    std::cout<<"UDP measurements: meanSquare="<<energy/measured<<" stereoError="<<stereoError<<" Hz="<<hz<<std::endl;
    assert(energy/measured>0.05 && stereoError<1e-4 && std::fabs(hz-1000)<15);
    for(int i=0;i<400;++i) { plugin.process(ctx); }
    assert(l[127]==0 && r[127]==0);
    std::string text; plugin.formatValue(Connection,0,text); assert(text=="RECEIVING");
    std::this_thread::sleep_for(850ms); waitText(Connection,"WAITING");
    // ANY accepts the next sender without configuring a stream-name filter.
    for(uint32_t seq: {0xfffffffeu,0xffffffffu,0u,3u,3u,2u}) send(seq,"iPhone",1,2,16);
    std::this_thread::sleep_for(150ms);
    waitText(StreamName,"iPhone");
    waitText(Lost,"Lost: 1");
    plugin.formatValue(Format,0,text); assert(text.find("24-bit Mono")!=std::string::npos);
    // A different stream cannot take over the active sender even in ANY.
    std::this_thread::sleep_for(850ms);
    send(0,"Android",2,4,3); send(1,"Android",2,4,3); send(2,"iPhone",1,1,16);
    std::this_thread::sleep_for(150ms); waitText(StreamName,"Android");
    plugin.formatValue(Format,0,text); assert(text.find("Float32 Stereo")!=std::string::npos);
    plugin.prepare(48000,512); plugin.process(ctx); // safe host-rate transition
    close(sock);
    std::cout<<"PASS UDP loopback: PCM16 stereo 48k->44.1k, pitch="<<hz<<" Hz, timeout, ANY-only sender lock, PCM24 mono, float32, sequence wrap/loss/duplicates, host-rate change\n";
}
