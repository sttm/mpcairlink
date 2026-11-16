#pragma once
#include "StreamCore.h"

namespace airlink {
// Worker-only bounded packet reorder queue. Sequence arithmetic is wrap-safe.
// Deadlines are measured from the first packet beyond a gap, not from silence.
class VbanQueue {
    static constexpr uint32_t Capacity=64;
public:
    struct Block {
        std::array<Stereo,256> audio{};
        uint32_t sequence=0,arrival=0;
        int frames=0,rate=0,channels=0,format=0;
        bool valid=false;
    };
private:
    std::array<Block,Capacity> blocks{};
    bool started=false;
    uint32_t expected=0;
    int previousFrames=128;
public:
    void reset() { for(auto& b:blocks) b.valid=false; started=false; previousFrames=128; }
    bool pending() const { for(const auto& b:blocks) if(b.valid) return true; return false; }
    template<class Emit,class Missing>
    void drain(uint32_t now,uint32_t wait,Emit&& emit,Missing&& missing) {
        if(!started) return;
        for(uint32_t attempts=0;attempts<Capacity*2;++attempts) {
            auto& next=blocks[expected&(Capacity-1)];
            if(next.valid && next.sequence==expected) {
                previousFrames=next.frames; emit(next); next.valid=false; ++expected; continue;
            }
            bool future=false; uint32_t oldestAge=0;
            for(const auto& b:blocks) if(b.valid) {
                uint32_t ahead=b.sequence-expected;
                if(ahead>0 && ahead<0x80000000u) {future=true; oldestAge=std::max(oldestAge,now-b.arrival);}
            }
            if(!future || oldestAge<wait) break;
            missing(1u,previousFrames); ++expected;
        }
    }
    template<class Emit,class Missing>
    bool push(const Packet& p,uint32_t now,uint32_t wait,Emit&& emit,Missing&& missing) {
        if(!started) {started=true; expected=p.sequence; previousFrames=p.frames;}
        uint32_t ahead=p.sequence-expected;
        if(ahead>=0x80000000u) return false; // already played/concealed: late or duplicate
        if(ahead>=Capacity) {
            // Large discontinuity: bounded concealment, no unbounded work or huge queue.
            missing(ahead<100000?ahead:0u,std::min(previousFrames*int(Capacity),p.rate/10));
            for(auto& b:blocks) b.valid=false;
            expected=p.sequence;
        }
        auto& slot=blocks[p.sequence&(Capacity-1)];
        if(slot.valid && slot.sequence==p.sequence) return false;
        slot.sequence=p.sequence; slot.arrival=now; slot.frames=p.frames;
        slot.rate=p.rate; slot.channels=p.channels; slot.format=p.format;
        for(int i=0;i<p.frames;++i) slot.audio[size_t(i)]={p.sample(i,0),p.sample(i,p.channels==2?1:0)};
        slot.valid=true;
        drain(now,wait,emit,missing);
        return true;
    }
};
}
