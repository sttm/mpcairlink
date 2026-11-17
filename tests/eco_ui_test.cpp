// Real VST entry, UDP audio and deliberately slow host UI callbacks.
#include <atomic>
static std::atomic<unsigned> meterSamples{0};
#define AIRLINK_METER_FRAME_HOOK() meterSamples.fetch_add(1,std::memory_order_relaxed)
#include "../src/MPCAirLink.cpp"
#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>
#include <cassert>
#include <iostream>
static std::array<std::atomic<unsigned>,16> calls{};
static std::atomic<unsigned> total{0},audioNotifications{0};
static std::thread::id audioThread;
static VstIntPtr host(AEffect*,VstInt32 op,VstInt32 index,VstIntPtr,void*,float){
 if(op==audioMasterVersion)return 2400;
 if(op==audioMasterAutomate){++total;if(index>=0&&index<16)++calls[index];if(std::this_thread::get_id()==audioThread)++audioNotifications;std::this_thread::sleep_for(std::chrono::milliseconds(8));}
 return 0;
}
int main(){
 audioThread=std::this_thread::get_id();AEffect* fx=VSTPluginMain(host);assert(fx&&fx->numParams==16);
 fx->dispatcher(fx,effOpen,0,0,nullptr,0);fx->dispatcher(fx,effSetSampleRate,0,0,nullptr,44100);fx->dispatcher(fx,effSetBlockSize,0,128,nullptr,0);
 assert(fx->getParameter(fx,14)==0); // AirPlay default; public selector has two options.
 fx->setParameter(fx,14,1);fx->setParameter(fx,2,1);fx->dispatcher(fx,effMainsChanged,0,1,nullptr,0);
 std::this_thread::sleep_for(std::chrono::milliseconds(1400));total=0;
 auto idleStart=std::chrono::steady_clock::now();auto idleSamples=meterSamples.load();
 std::this_thread::sleep_for(std::chrono::milliseconds(1100));assert(total.load()==0);
 double hz24=(meterSamples.load()-idleSamples)/std::chrono::duration<double>(std::chrono::steady_clock::now()-idleStart).count();assert(hz24>=22&&hz24<=26);
 fx->setParameter(fx,15,0);std::this_thread::sleep_for(std::chrono::milliseconds(250));
 idleStart=std::chrono::steady_clock::now();idleSamples=meterSamples.load();std::this_thread::sleep_for(std::chrono::milliseconds(1100));
 double hz10=(meterSamples.load()-idleSamples)/std::chrono::duration<double>(std::chrono::steady_clock::now()-idleStart).count();assert(hz10>=9&&hz10<=11);
 fx->setParameter(fx,15,1);std::this_thread::sleep_for(std::chrono::milliseconds(200));
 std::cout<<"Measured idle meter sampling: "<<hz24<<" Hz / "<<hz10<<" Hz; no notifications for unchanged blocks\n";
 int sock=socket(AF_INET,SOCK_DGRAM,0);assert(sock>=0);sockaddr_in to{};to.sin_family=AF_INET;to.sin_port=htons(6980);inet_pton(AF_INET,"127.0.0.1",&to.sin_addr);
 std::atomic<bool> sending{true};
 std::thread sender([&]{auto next=std::chrono::steady_clock::now();uint32_t sequence=0;while(sending.load()){
  std::array<uint8_t,1052> b{};std::memcpy(b.data(),"VBAN",4);b[4]=3;b[5]=255;b[6]=1;b[7]=1;std::memcpy(b.data()+8,"EcoTest",7);
  for(int j=0;j<4;++j)b[24+j]=uint8_t(sequence>>(j*8));
  int amplitude=int(3000+10000*(.5+.5*std::sin(sequence*256./48000*2*3.141592653589793*4)));
  for(int j=0;j<256;++j)for(int ch=0;ch<2;++ch){int sample=ch?-amplitude:amplitude;size_t p=28+size_t(j*2+ch)*2;b[p]=uint8_t(sample);b[p+1]=uint8_t(sample>>8);}
  assert(sendto(sock,b.data(),b.size(),0,reinterpret_cast<sockaddr*>(&to),sizeof(to))==ssize_t(b.size()));++sequence;
  next+=std::chrono::nanoseconds(5333333);std::this_thread::sleep_until(next);
 }});
 for(auto& c:calls){c=0;}
 float l[128]{},r[128]{};float* output[]={l,r};double energy=0;auto next=std::chrono::steady_clock::now();
 for(int block=0;block<800;++block){fx->processReplacing(fx,nullptr,output,128);for(int j=0;j<128;++j){assert(std::isfinite(l[j])&&std::isfinite(r[j]));if(block>100)energy+=l[j]*l[j];}next+=std::chrono::nanoseconds(2902494);std::this_thread::sleep_until(next);}
 sending=false;sender.join();close(sock);assert(energy>100);
 assert(fx->getParameter(fx,11)==0&&fx->getParameter(fx,12)==0);
 assert(calls[9].load()>=24&&calls[10].load()>=24&&calls[9].load()<=58&&calls[10].load()<=58&&audioNotifications.load()==0);
 std::cout<<"PASS idle zero UI notifications; 24 Hz target, changing-meter callbacks over 2.32s: "<<calls[9]<<"/"<<calls[10]<<"; continuous UDP audio under slow UI host, no UI calls from audio thread\n";
 fx->dispatcher(fx,effMainsChanged,0,0,nullptr,0);fx->dispatcher(fx,effClose,0,0,nullptr,0);
}
