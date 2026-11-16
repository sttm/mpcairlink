# MPC AirLink 1.0.0 validation

Identity: mpcairlink / ArLk / MPC AirLink by sttm.
Both ARM targets built in Docker linux/amd64 using GNU C++17.
SDK validator: 0 errors, 0 warnings. Terminal STREAM and DIAG tabs valid.
Native host: 18 PASS, one expected silence warning without a network sender.
VBAN: PCM16/24/float32, mono/stereo, ANY-only ownership, resampling,
packet reorder/loss/duplicates/wrap, repeated host resume/reset.
Real UDP loss test: injected six lost packets, six counted; zero FIFO drops/underruns.
AirPlay: mDNS advertises MPC AirLink, RSA challenge, RTSP/RTP PCM and encrypted ALAC.
Tac: actual Swift sender -> new VST2, 256 frames, no UDP send errors or lost packets.
ASan/UBSan: core, UDP, reorder and injected-loss tests passed.
Archive identity/content/CRC and SHA256 checked.

Physical MPC Key 61 / OS 3.10.1: user confirmed this AirLink build works, 2026-11-16.
Gen2 hardware remains untested. Touch/Q-Link and long-duration operation were not
individually reported. Old-project migration uses a separate UID intentionally.
Source folder remains the shared workspace; install folder and binaries use AirLink.
