#include "VbanQueue.h"
#include <cassert>
#include <iostream>
#include <vector>
using namespace airlink;
int main() {
    VbanQueue q;
    std::vector<uint32_t> played;
    uint32_t lost=0; int concealed=0;
    auto emit=[&](const VbanQueue::Block& b){played.push_back(b.sequence); assert(b.frames==256 && b.audio[0].l==.25f);};
    auto missing=[&](uint32_t packets,int frames){lost+=packets; concealed+=frames;};
    auto send=[&](uint32_t sequence,uint32_t time) {
        std::array<uint8_t,1052> b{}; std::memcpy(b.data(),"VBAN",4); b[4]=3; b[5]=255; b[6]=1; b[7]=1;
        for(int k=0;k<4;++k) b[24+k]=uint8_t(sequence>>(8*k));
        for(int i=0;i<512;++i) b[28+i*2+1]=32;
        Packet p; assert(p.parse(b.data(),b.size())); return q.push(p,time,12,emit,missing);
    };
    assert(send(0xfffffffeu,0)); assert(send(0u,1)); assert(send(0xffffffffu,10));
    assert((played==std::vector<uint32_t>{0xfffffffeu,0xffffffffu,0u}));
    assert(lost==0 && concealed==0 && !q.pending());
    assert(send(3u,11)); assert(send(2u,12)); assert(!send(2u,13));
    q.drain(22,12,emit,missing); assert(lost==0);
    q.drain(23,12,emit,missing); assert(lost==1 && concealed==256);
    assert((played==std::vector<uint32_t>{0xfffffffeu,0xffffffffu,0u,2u,3u}));
    assert(!send(1u,24)); assert(!send(3u,24)); assert(lost==1);
    assert(send(10000,25)); assert(lost==9997 && concealed<=256+4800);
    q.reset(); played.clear(); lost=0; concealed=0;
    assert(send(10,100)); assert(send(12,101)); assert(send(13,102)); assert(send(11,108));
    assert((played==std::vector<uint32_t>{10,11,12,13}) && lost==0);
    // No fill during a stopped stream: empty queue cannot manufacture an endless silent stream.
    q.drain(1000000,12,emit,missing); assert(lost==0 && !q.pending());
    std::cout<<"PASS VBAN reorder, uint32 wrap, duplicates, gap deadline, time-preserving concealment, bounded restart, idle\n";
}
