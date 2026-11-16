#pragma once
#include "StreamCore.h"
#include "AirPlayProcess.h"
#include <thread>
#include <functional>
#include <string>

namespace airlink {
struct Status {
    std::string ip="NO LAN IPv4", name="--";
    int rate=0,format=0,channels=0,error=0;
    uint32_t lost=0,overflows=0;
    bool receiving=false, airplayReady=false;
    int airplayError=0;
    std::string source="--";
};
class Receiver {
public:
    Ring<32768> ring;
    std::atomic<int> hostRate{44100}, mode{0}, activeSource{0}, latencyMs{40};
    std::string contentDirectory;
    std::atomic<uint32_t> epoch{0};
    // Called only on the worker, never on audio. Owner must join before destruction.
    std::function<void(const Status&)> onStatus;
    void start() { running.store(true); thread=std::thread([this]{run();}); }
    void stop() { running.store(false); if(thread.joinable()) thread.join(); }
    ~Receiver() { stop(); }
private:
    std::atomic<bool> running{false};
    std::thread thread;
    void run();
};
}
