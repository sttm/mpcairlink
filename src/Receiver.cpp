#include "Receiver.h"
#include "VbanQueue.h"
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <ifaddrs.h>
#include <net/if.h>
#include <unistd.h>
#include <poll.h>
#include <fcntl.h>
#include <cerrno>
#include <chrono>
#include <pthread.h>
#include <sched.h>

namespace airlink {
using Clock=std::chrono::steady_clock;
static std::string localIP() {
    ifaddrs* list=nullptr; if(getifaddrs(&list)) return "NO LAN IPv4";
    std::string result="NO LAN IPv4"; int best=-1;
    for(auto* p=list;p;p=p->ifa_next) {
        if(!p->ifa_addr || p->ifa_addr->sa_family!=AF_INET || !(p->ifa_flags&IFF_UP) || (p->ifa_flags&IFF_LOOPBACK)) continue;
        auto* a=reinterpret_cast<sockaddr_in*>(p->ifa_addr); uint32_t ip=ntohl(a->sin_addr.s_addr);
        bool priv=(ip>>24)==10 || (ip>>20)==0xac1 || (ip>>16)==0xc0a8;
        std::string name=p->ifa_name;
        int score=(priv?10:0)+(name.rfind("wlan",0)==0 || name.rfind("eth",0)==0 || name.rfind("en",0)==0?5:0);
        char b[INET_ADDRSTRLEN]; if(score>best && inet_ntop(AF_INET,&a->sin_addr,b,sizeof b)) { result=b; best=score; }
    }
    freeifaddrs(list); return result;
}
void Receiver::run() {
    sched_param normal{};(void)pthread_setschedparam(pthread_self(),SCHED_OTHER,&normal);
    Status status; status.ip=localIP();
    int fd=socket(AF_INET,SOCK_DGRAM|SOCK_CLOEXEC,0);
    if(fd<0) status.error=errno;
    if(fd>=0) {
        int yes=1,buf=1048576; setsockopt(fd,SOL_SOCKET,SO_REUSEADDR,&yes,sizeof yes);
        setsockopt(fd,SOL_SOCKET,SO_RCVBUF,&buf,sizeof buf);
        int flags=fcntl(fd,F_GETFL,0);
        sockaddr_in addr{}; addr.sin_family=AF_INET; addr.sin_port=htons(6980); addr.sin_addr.s_addr=htonl(INADDR_ANY);
        if(flags<0 || fcntl(fd,F_SETFL,flags|O_NONBLOCK)<0 || bind(fd,reinterpret_cast<sockaddr*>(&addr),sizeof addr)<0) { status.error=errno; close(fd); fd=-1; }
    }
    std::array<uint8_t,65536> bytes{};
    std::array<char,17> active{};
    sockaddr_in source{};
    bool locked=false;
    int oldHost=0,oldRate=0,oldFormat=0,oldChannels=0,oldMode=-1;
    int activeProtocol=0; // 0 idle, 1 VBAN, 2 AirPlay. Single producer owns both inputs.
    AirPlayProcess airplay;
    std::array<uint8_t,16384> pcm{}; size_t carry=0;
    Resampler airplayResampler;
    Resampler resampler;
    VbanQueue ordered;
    Stereo lastVban{};
    bool recovering=false;
    auto last=Clock::now(),ui=last-std::chrono::seconds(1),ipTime=last;
    auto resetStream=[&] { locked=false; ordered.reset(); lastVban={}; recovering=false; status.receiving=false; status.name="--"; status.rate=0; status.source="--"; activeProtocol=0; activeSource.store(0,std::memory_order_release); resampler.reset(); airplayResampler.reset(); epoch.fetch_add(1,std::memory_order_release); };
    while(running.load()) {
        auto now=Clock::now(); int rate=hostRate.load(),receiveMode=mode.load();
        if(receiveMode!=oldMode) {
            if(oldMode<0 || (receiveMode==1 && activeProtocol==2) || (receiveMode==2 && activeProtocol==1)) resetStream();
            if(receiveMode==1) {airplay.stop(); carry=0;}
            else if(oldMode<0 || oldMode==1) {airplay.start(contentDirectory); carry=0;}
            oldMode=receiveMode;
        }
        status.airplayReady=receiveMode!=1 && airplay.alive();
        status.airplayError=receiveMode==1?0:airplay.error;
        if(rate!=oldHost) {resampler.reset(); airplayResampler.reset(); epoch.fetch_add(1,std::memory_order_release); oldHost=rate;}
        if(locked && now-last>std::chrono::milliseconds(700)) resetStream();
        if(now-ipTime>std::chrono::seconds(3)) { status.ip=localIP(); ipTime=now; }
        if(now-ui>=std::chrono::milliseconds(100)) { if(onStatus) onStatus(status); ui=now; }
        auto milliseconds=[] {return uint32_t(std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now().time_since_epoch()).count());};
        uint32_t reorderWait=uint32_t(std::clamp(latencyMs.load()/4,2,12));
        std::array<Stereo,256> converted{}; uint32_t convertedCount=0;
        auto flush=[&] {
            if(convertedCount) {status.overflows+=convertedCount-ring.pushMany(converted.data(),convertedCount); convertedCount=0;}
        };
        auto output=[&](Stereo frame) {
            resampler.feed(frame,double(oldRate)/std::max(8000,rate),[&](Stereo out){converted[convertedCount++]=out; if(convertedCount==converted.size()) flush();});
        };
        auto deliver=[&](const VbanQueue::Block& block) {
            Stereo start=lastVban;
            for(int i=0;i<block.frames;++i) {
                Stereo frame=block.audio[size_t(i)];
                if(recovering && i<32) {float t=float(i+1)/32; frame={start.l+(frame.l-start.l)*t,start.r+(frame.r-start.r)*t};}
                output(frame); lastVban=frame;
            }
            recovering=false;
        };
        auto missing=[&](uint32_t packets,int frames) {
            status.lost+=packets;
            for(int i=0;i<frames;++i) {lastVban.l*=0.98f; lastVban.r*=0.98f; if(std::fabs(lastVban.l)<1e-8f) lastVban.l=0; if(std::fabs(lastVban.r)<1e-8f) lastVban.r=0; output(lastVban);}
            recovering=true;
        };
        if(activeProtocol==1) ordered.drain(milliseconds(),reorderWait,deliver,missing);
        flush();
        pollfd pf[2]={{fd,POLLIN,0},{status.airplayReady?airplay.fd():-1,POLLIN,0}};
        int ready=poll(pf,2,ordered.pending()?2:20); if(ready<=0) continue;
        if(pf[1].revents&POLLIN) {
            ssize_t amount=read(airplay.fd(),pcm.data()+carry,pcm.size()-carry);
            if(amount>0) {
                size_t total=carry+size_t(amount),frames=total/4;
                if(receiveMode!=1 && (activeProtocol==0 || activeProtocol==2)) {
                    if(activeProtocol==0) { activeProtocol=2; activeSource.store(2,std::memory_order_release); locked=true; airplayResampler.reset(); epoch.fetch_add(1,std::memory_order_release); }
                    last=now; status.receiving=true; status.source="AirPlay"; status.name="AirPlay";
                    status.rate=44100; status.channels=2; status.format=1;
                    for(size_t i=0;i<frames;++i) {
                        auto decode=[](const uint8_t* p) {int v=int(p[0])+(int(p[1])<<8); if(v&0x8000) v-=65536; return float(v)/32768.f;};
                        Stereo s{decode(pcm.data()+i*4),decode(pcm.data()+i*4+2)};
                        airplayResampler.feed(s,44100.0/std::max(8000,rate),[&](Stereo out){if(!ring.push(out)) ++status.overflows;});
                    }
                }
                carry=total%4; if(carry) std::memmove(pcm.data(),pcm.data()+frames*4,carry);
            }
        }
        if(!(pf[0].revents&POLLIN)) continue;
        // Drain queued datagrams in a bounded batch instead of waking once per packet.
        for(int batch=0;batch<64;++batch) {
            sockaddr_in sender{}; socklen_t len=sizeof sender;
            ssize_t n=recvfrom(fd,bytes.data(),bytes.size(),0,reinterpret_cast<sockaddr*>(&sender),&len);
            if(n<0) break;
            Packet p; if(receiveMode==2 || activeProtocol==2 || !p.parse(bytes.data(),size_t(n))) continue;
            if(locked && (active!=p.name || source.sin_addr.s_addr!=sender.sin_addr.s_addr || source.sin_port!=sender.sin_port)) continue;
            if(!locked) { activeProtocol=1; activeSource.store(1,std::memory_order_release); status.source="VBAN"; active=p.name; source=sender; locked=true; ordered.reset(); resampler.reset(); lastVban={}; recovering=false; }
            if(p.rate!=oldRate || p.format!=oldFormat || p.channels!=oldChannels) {
                oldRate=p.rate; oldFormat=p.format; oldChannels=p.channels; ordered.reset(); resampler.reset(); lastVban={}; recovering=false; epoch.fetch_add(1,std::memory_order_release);
            }
            if(!ordered.push(p,milliseconds(),reorderWait,deliver,missing)) continue;
            last=Clock::now();
            status.name=p.name.data(); status.rate=p.rate; status.format=p.format; status.channels=p.channels; status.receiving=true;
        }
        flush();
    }
    if(fd>=0) close(fd);
}
}
