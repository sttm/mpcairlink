// Deterministic virtual-time listening test, not a Wi-Fi/device measurement.
#include "StreamCore.h"
#include <cassert>
#include <chrono>
#include <iostream>
using namespace airlink;
int main(){
 auto begin=std::chrono::steady_clock::now();
 for(double speed:{.999,1.001}){
  Ring<32768> fifo;Renderer renderer;Resampler resampler;
  uint64_t packets=0;double arrival=0;uint32_t overflow=0;float l[128]{},r[128]{};
  constexpr double hostRate=44100,senderRate=48000,seconds=600;
  int threshold=speed<1?4410:6615; // 100 / 150 ms listening profiles.
  for(int block=0;block<int(seconds*hostRate/128);++block){
   double now=block*128./hostRate;
   while(arrival<=now){
    for(int j=0;j<256;++j)resampler.feed({.25f,-.25f},senderRate/hostRate,[&](Stereo frame){if(!fifo.push(frame))++overflow;});
    ++packets;arrival=packets*256./(senderRate*speed)+(packets%2?.0015:-.0015);
   }
   renderer.render(fifo,l,r,128,threshold,1,true,int(hostRate));
   if(now>2){assert(l[127]>.20f&&std::abs(l[127]+r[127])<1e-6f);}
   assert(std::isfinite(l[127])&&std::isfinite(r[127]));
  }
  assert(overflow==0&&renderer.underruns.load()==0&&renderer.discarded.load()==0);
  std::cout<<"PASS 10 simulated minutes: VBAN 256 frames, 48k->44.1k, "<<speed<<" sender clock, +/-1.5ms jitter, zero overflow/trim/underrun\n";
 }
 std::cout<<"20 simulated minutes completed in "<<std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count()<<" wall seconds; this is not a real-network soak\n";
}
