#include "StreamCore.h"
#include <cassert>
#include <iostream>
using namespace airlink;
int main() {
    // Reproduce a 4096-frame stdout burst: 1.1.0 discarded valid PCM above target+2048.
    Ring<32768> ring; Renderer r;
    for(int i=0;i<6000;++i) assert(ring.push({.25f,-.25f}));
    float l[128]{},rr[128]{};
    r.render(ring,l,rr,128,1764,1,true);
    assert(r.discarded.load()==0 && ring.size()>5800);
    // 3 simulated minutes per clock offset, packet delivery in 93 ms bursts with +-15 ms jitter.
    for(double speed: {0.999,1.001}) {
        Ring<32768> fifo; Renderer renderer;
        double generated=0,nextBurst=0; bool started=false; int silence=0;
        for(int block=0;block<62016;++block) {
            double time=block*128./44100;
            while(time>=nextBurst) {
                for(int f=0;f<4096;++f) assert(fifo.push({.25f,-.25f}));
                generated+=4096;
                int burst=int(generated/4096);
                nextBurst=generated/(44100*speed)+(burst%2?0.015:-0.015);
            }
            renderer.render(fifo,l,rr,128,5292,1,true);
            if(time>1) {started=true; if(l[127]<.2f) ++silence;}
        }
        assert(started && silence==0 && renderer.underruns.load()==0 && renderer.discarded.load()==0);
    }
    std::cout<<"PASS AirPlay-sized bursts preserved; 6 simulated minutes with jitter and +/-1000 ppm clocks: zero underruns/drops\n";
}
