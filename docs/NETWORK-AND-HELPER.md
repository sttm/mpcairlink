# Network and bundled helper review notes

MPC AirLink intentionally receives LAN audio. The catalog scanner will report network and process APIs; these are functional requirements, not reviewed/approved flags.

- The VST binds IPv4 UDP 6980 for VBAN reception. It determines displayable local IPv4 addresses through getifaddrs. It does not contact an Internet service or download code at runtime.
- AirPlay (the default source) launches the bundled, architecture-matched Shairport Sync 4.3.7 helper with posix_spawn. VBAN stops it. Network and process work happens on the worker, not in the audio callback.
- A private mkdtemp directory under /tmp holds an executable copy (0700), a generated fixed configuration and stderr log. The child receives stdout through a pipe, stdin=/dev/null, and only LANG, PATH and a helper-only LD_LIBRARY_PATH. File descriptors from 3 upwards are closed in the child. This is process separation, not a security sandbox.
- Generated configuration selects the fixed name MPC AirLink, TCP 5000, stdout PCM output, TinySVCmDNS and basic interpolation. No user-supplied command, start/stop hook or external audio backend is configured. No system service, firmware change or privileged installation is requested.
- AirPlay advertises via mDNS UDP 5353, accepts RTSP TCP 5000 and uses negotiated UDP audio/control/timing ports. RAOP uses OpenSSL for RSA/AES. Classic RAOP is intended for a trusted LAN and this MVP provides no receiver password UI.
- SIGTERM (with bounded SIGKILL fallback) stops the owned child on mode changes/unload. The pipe, executable, configuration, log and private directory are cleaned up. Abrupt host termination can leave temporary files until reboot.

The scanner also reports exported capabilities in bundled upstream binaries: OpenSSL has network/dlopen functions, libpopt includes execvp/setuid/setgid, and Shairport includes optional hook execution functions. These symbols are not hidden or removed to bypass review. AirLink uses a fixed generated configuration and does not configure such hooks. Review the vendored source, helper configure flags and generated configuration in `src/AirPlayProcess.cpp` and `tools/build_airplay.sh`.

Only maintainers should set `flags_reviewed` in the catalog. This submission does not set it.

## Helper build licence audit — 1.1.1

Classic AirPlay is built without CONFIG_AIRPLAY_2 and CONFIG_CONVOLUTION.
Upstream conditional rules exclude ptp-utilities.c / nqptp-shm-structures.h and
FFTConvolver sources in this configuration. Compiler dependency files are checked
for both architectures; the build evidence and helper digests are recorded in
[LICENSE-AUDIT.json](LICENSE-AUDIT.json). The bundled upstream GPL-2.txt and
GPL-3.txt notices are copied unconditionally and do not indicate enabled features.
This audit concerns this configuration, not every possible Shairport Sync build.

The distributed code licence expression is MIT AND BSD-3-Clause AND Apache-2.0
AND LGPL-2.1-or-later. Font and CC0 icon notices stay in the repo/package; they do
not require a change to the catalog's global OPEN_LICENSES policy.
