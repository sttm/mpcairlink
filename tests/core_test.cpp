#include "StreamCore.h"
#include <cassert>
#include <thread>
#include <iostream>
#include <vector>
using namespace airlink;
int main() {
    std::array<uint8_t,40> b{}; std::memcpy(b.data(),"VBAN",4); b[4]=3; b[5]=1; b[6]=1; b[7]=1; std::memcpy(b.data()+8,"Stream1",7);
    b[28]=0; b[29]=128; b[30]=255; b[31]=127;
    Packet p; assert(p.parse(b.data(),36)); assert(p.rate==48000 && p.frames==2 && p.channels==2);
    assert(p.sample(0,0)==-1); assert(std::fabs(p.sample(0,1)-32767.f/32768)<1e-7);
    assert(!p.parse(b.data(),27)); assert(!p.parse(b.data(),35)); assert(!p.parse(b.data(),37));
    for(int sr=0;sr<21;++sr) { b[4]=uint8_t(sr); assert(p.parse(b.data(),36)); assert(p.rate==Packet::rates[sr]); }
    b[4]=21; assert(!p.parse(b.data(),36)); b[4]=0x23; assert(!p.parse(b.data(),36)); b[4]=3;
    b[7]=0x11; assert(!p.parse(b.data(),36)); b[7]=2; b[5]=0; b[6]=0;
    b[28]=0; b[29]=0; b[30]=128; assert(p.parse(b.data(),31)); assert(p.sample(0,0)==-1);
    b[28]=255; b[29]=255; b[30]=127; assert(p.parse(b.data(),31)); assert(p.sample(0,0)>0.99999f);
    b[7]=4; b[28]=0; b[29]=0; b[30]=128; b[31]=63; assert(p.parse(b.data(),32)); assert(p.sample(0,0)==1);
    b[30]=192; b[31]=127; assert(p.parse(b.data(),32)); assert(p.sample(0,0)==0); // NaN sanitized
    Ring<1024> ring;
    std::thread producer([&]{for(int i=0;i<1000000;++i) while(!ring.push({float(i),-float(i)})) std::this_thread::yield();});
    for(int i=0;i<1000000;++i) { Stereo s; while(!ring.pop(s)) std::this_thread::yield(); assert(s.l==float(i) && s.r==-float(i)); }
    producer.join(); assert(ring.size()==0);
    Ring<1024> batched;
    std::thread batchProducer([&]{
        std::array<Stereo,37> frames{}; uint32_t sent=0;
        while(sent<100003) {
            uint32_t n=std::min(37u,100003-sent);
            for(uint32_t k=0;k<n;++k) frames[k]={float(sent+k),-float(sent+k)};
            sent+=batched.pushMany(frames.data(),n);
        }
    });
    for(uint32_t i=0;i<100003;++i) {Stereo frame; while(!batched.pop(frame)) std::this_thread::yield(); assert(frame.l==float(i) && frame.r==-float(i));}
    batchProducer.join();
    for(auto rates: {std::pair<int,int>{48000,44100},{44100,48000},{6000,192000},{705600,44100}}) {
        Resampler rs; int count=0; double error=0;
        for(int i=0;i<rates.first;++i) {
            float x=float(std::sin(2*3.141592653589793*440*i/rates.first));
            rs.feed({x,x},double(rates.first)/rates.second,[&](Stereo s){
                double expected=std::sin(2*3.141592653589793*440*count/rates.second); error+=std::pow(s.l-expected,2); assert(s.l==s.r); ++count;
            });
        }
        assert(std::abs(count-rates.second)<=32); assert(std::sqrt(error/count)<0.03);
    }
    Ring<1024> audio; Renderer r; float l[256]{},rr[256]{};
    for(int i=0;i<199;++i) assert(audio.push({0.5f,-0.5f}));
    r.render(audio,l,rr,128,200,1); assert(l[127]==0 && audio.size()==199);
    assert(audio.push({0.5f,-0.5f})); r.render(audio,l,rr,128,200,1);
    assert(l[0]>0 && l[0]<0.01 && l[127]==0.5f && rr[127]==-0.5f);
    r.render(audio,l,rr,256,200,1); assert(r.underruns.load()==1); assert(std::fabs(l[255])<0.002f);
    std::cout<<"PASS parser (PCM16/24/float/NaN/malformed/rates), million-frame concurrent SPSC, rate conversion, prebuffer/fades\n";
}
