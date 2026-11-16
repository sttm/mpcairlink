#pragma once
#include <string>
#include <sys/types.h>

namespace airlink {
// Worker-owned child process. Its stdout is PCM16 LE stereo 44100 Hz.
// Child-only libraries never enter the MPC audio process.
class AirPlayProcess {
    pid_t child=-1;
    int audio=-1;
    std::string runtime;
public:
    int error=0;
    bool start(const std::string& content);
    void stop();
    bool alive();
    int fd() const { return audio; }
    ~AirPlayProcess() { stop(); }
};
}
