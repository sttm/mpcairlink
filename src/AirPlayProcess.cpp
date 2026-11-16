#include "AirPlayProcess.h"
#include <spawn.h>
#include <sys/wait.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <signal.h>
#include <cerrno>
#include <cstdio>
#include <cstring>
#include <vector>
#include <thread>
#include <chrono>

namespace airlink {
static bool copyExecutable(const std::string& from,const std::string& to) {
    int in=open(from.c_str(),O_RDONLY|O_CLOEXEC); if(in<0) return false;
    int out=open(to.c_str(),O_CREAT|O_EXCL|O_WRONLY|O_CLOEXEC,0700);
    if(out<0) { int e=errno; close(in); errno=e; return false; }
    char b[16384]; bool okay=true;
    while(true) {
        ssize_t n=read(in,b,sizeof b); if(n<0 && errno==EINTR) continue;
        if(n<=0) { if(n<0) okay=false; break; }
        ssize_t offset=0;
        while(offset<n) { ssize_t w=write(out,b+offset,size_t(n-offset)); if(w<0 && errno==EINTR) continue; if(w<=0) {okay=false; break;} offset+=w; }
        if(!okay) break;
    }
    int e=errno; close(in); close(out); errno=e; return okay;
}
bool AirPlayProcess::start(const std::string& content) {
    stop(); error=0;
#if defined(__arm__)
    const char* arch="arm32";
#elif defined(__aarch64__)
    const char* arch="arm64";
#else
    const char* arch="native";
#endif
    char directory[]="/tmp/mpcairlink-airplay-XXXXXX";
    if(!mkdtemp(directory)) {error=errno; return false;}
    runtime=directory;
    const std::string executable=runtime+"/receiver";
    if(!copyExecutable(content+"/AirPlay/shairport-sync-"+arch,executable)) {error=errno; stop(); return false;}
    std::string config=runtime+"/receiver.conf";
    FILE* f=std::fopen(config.c_str(),"w");
    if(!f) {error=errno; stop(); return false;}
    std::fputs("general = { name = \"MPC AirLink\"; port = 5000; output_backend = \"stdout\"; mdns_backend = \"tinysvcmdns\"; interpolation = \"basic\"; audio_backend_buffer_desired_length_in_seconds = 0.10; };\ndiagnostics = { log_output_to = \"stderr\"; log_verbosity = 0; };\n",f);
    std::fclose(f);
    int ends[2]; if(pipe2(ends,O_CLOEXEC)) {error=errno; stop(); return false;}
    fcntl(ends[0],F_SETFL,O_NONBLOCK);
    posix_spawn_file_actions_t actions;
    posix_spawn_file_actions_init(&actions);
    posix_spawn_file_actions_adddup2(&actions,ends[1],STDOUT_FILENO);
    posix_spawn_file_actions_addclose(&actions,ends[0]);
    posix_spawn_file_actions_addclose(&actions,ends[1]);
    posix_spawn_file_actions_addopen(&actions,STDIN_FILENO,"/dev/null",O_RDONLY,0);
    posix_spawn_file_actions_addopen(&actions,STDERR_FILENO,(runtime+"/receiver.log").c_str(),O_CREAT|O_WRONLY|O_TRUNC,0600);
    posix_spawn_file_actions_addclosefrom_np(&actions,3); // Do not inherit MPC device/socket handles.
    // A minimal private environment avoids inheriting host LD_PRELOAD or library paths.
    std::string library="LD_LIBRARY_PATH="+content+"/AirPlay/lib-"+arch;
    char lang[]="LANG=C", path[]="PATH=/usr/bin:/bin";
    char* env[]={library.data(),lang,path,nullptr};
    char* args[]={const_cast<char*>(executable.c_str()),const_cast<char*>("-c"),const_cast<char*>(config.c_str()),nullptr};
    int result=posix_spawn(&child,executable.c_str(),&actions,nullptr,args,env);
    posix_spawn_file_actions_destroy(&actions); close(ends[1]);
    if(result) {close(ends[0]); child=-1; error=result; stop(); return false;}
    audio=ends[0]; return true;
}
bool AirPlayProcess::alive() {
    if(child<0) return false;
    int status=0; pid_t rc=waitpid(child,&status,WNOHANG);
    if(rc==0 || (rc<0 && errno==EINTR)) return true;
    child=-1;
    error=rc<0?errno:WIFEXITED(status)?1000+WEXITSTATUS(status):2000+WTERMSIG(status);
    return false;
}
void AirPlayProcess::stop() {
    if(child>0) {
        kill(child,SIGTERM);
        bool done=false;
        for(int n=0;n<25;++n) {
            int status; auto rc=waitpid(child,&status,WNOHANG);
            if(rc==child || (rc<0 && errno==ECHILD)) {done=true; break;}
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }
        if(!done) { kill(child,SIGKILL); while(waitpid(child,nullptr,0)<0 && errno==EINTR) {} }
        child=-1;
    }
    if(audio>=0) {close(audio); audio=-1;}
    if(!runtime.empty()) {
        for(const char* name: {"/receiver","/receiver.conf","/receiver.log"}) unlink((runtime+name).c_str());
        rmdir(runtime.c_str()); runtime.clear();
    }
}
}
