#include "Receiver.h"
#include <arpa/inet.h>
#include <unistd.h>
#include <cassert>
#include <chrono>
#include <iostream>
#include <mutex>
using namespace std::chrono_literals;
int main() {
    airlink::Receiver receiver; receiver.mode.store(1); receiver.latencyMs.store(150);
    std::mutex lock; airlink::Status status;
    receiver.onStatus=[&](const airlink::Status& s){std::lock_guard<std::mutex> guard(lock); status=s;};
    receiver.start();
    int sock=socket(AF_INET,SOCK_DGRAM,0); assert(sock>=0);
    sockaddr_in dest{};dest.sin_family=AF_INET;dest.sin_port=htons(6980);inet_pton(AF_INET,"127.0.0.1",&dest.sin_addr);
    auto send=[&](uint32_t seq) {
        std::array<uint8_t,1052> b{};std::memcpy(b.data(),"VBAN",4);b[4]=3;b[5]=255;b[6]=1;b[7]=1;
        std::memcpy(b.data()+8,"Stream1",7);
        for(int k=0;k<4;++k)b[24+k]=uint8_t(seq>>(k*8));
        for(int i=0;i<512;++i)b[28+i*2+1]=32;
        assert(sendto(sock,b.data(),b.size(),0,reinterpret_cast<sockaddr*>(&dest),sizeof dest)==ssize_t(b.size()));
    };
    std::this_thread::sleep_for(100ms);
    std::atomic<bool> running{true};uint32_t deliberatelyLost=0;
    std::thread sender([&] {
        uint32_t sequence=0,held=0;bool holding=false;
        auto next=std::chrono::steady_clock::now();
        while(running.load()) {
            if(sequence%89==40){++deliberatelyLost;}
            else if(sequence%19==10){held=sequence;holding=true;}
            else {send(sequence);if(holding){send(held);holding=false;} if(sequence%101==99)send(sequence);}
            ++sequence; next+=std::chrono::nanoseconds(5333333);std::this_thread::sleep_until(next);
        }
    });
    airlink::Renderer renderer;float l[128]{},r[128]{};
    uint32_t epoch=0;int realAudio=0;auto next=std::chrono::steady_clock::now();
    for(int block=0;block<1050;++block) {
        auto observed=receiver.epoch.load();if(observed!=epoch){receiver.ring.discard();renderer.rebuffer();epoch=observed;}
        renderer.render(receiver.ring,l,r,128,6615,1,true);
        if(block>100 && l[127]>.1f)++realAudio;
        next+=std::chrono::nanoseconds(2902494);std::this_thread::sleep_until(next);
    }
    running.store(false);sender.join();std::this_thread::sleep_for(40ms);receiver.stop();close(sock);
    std::cout<<"Loss test: missing="<<status.lost<<" expected="<<deliberatelyLost<<" overflow="<<status.overflows<<" trim="<<renderer.discarded.load()<<" underruns="<<renderer.underruns.load()<<std::endl;
    assert(status.lost==deliberatelyLost && deliberatelyLost>=5);
    assert(status.overflows==0 && renderer.discarded.load()==0 && renderer.underruns.load()==0 && realAudio>900);
    std::cout<<"PASS real UDP: 256-frame VBAN, reorder+duplicates+1% loss, preserved timeline, zero FIFO drops/underruns\n";
}
