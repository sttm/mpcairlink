# MPC AirLink 1.3.0

Classic AirPlay / VBAN audio receiver for Akai MPC Standalone. Native VST2 instrument by **sttm**, with stereo output on its plugin track.

![Generated UI preview; not a hardware screenshot](docs/ui-preview.png)

[Русская инструкция](README.ru.md) · [Validation](docs/VALIDATION.md) · [Third-party notices](THIRD_PARTY.md)

## Install

Requires **MPC OS 3.10.1+**. Download `mpcairlink-1.3.0-mpc.zip` from [Releases](https://github.com/sttm/mpcairlink/releases/tag/v1.3.0), extract to SD/USB root and keep this complete folder:

`VST2 Plugins/sttm - VST - MPC AirLink/`

Enable Preferences → Enhancements (Beta) → Enable Enhancements and External Plugin Support, then restart MPC. Load External Plugins → sttm → MPC AirLink on a Plugin track and route it to the desired output. Leave the drive connected. MIDI notes and sequencer playback are not needed. The combined ZIP includes ARMv7 (Gen1) and AArch64 (Gen2); separate per-CPU catalog ZIPs are also published.

## Listen

- **Mac / iPhone:** join the same local network, leave AirPlay selected and choose **MPC AirLink** in the sender's AirPlay audio menu. This is classic RAOP audio, not screen mirroring or AirPlay 2. Normal AirPlay protocol latency still applies.
- **Windows / Android / other VBAN senders:** choose VBAN. Send to the displayed MPC IPv4 address, UDP 6980. Any stream name is accepted; PCM16/24 or float32, mono/stereo are supported. Prefer 44.1/48 kHz and 256 frames per packet. VBAN Talkie sends its microphone input and needs microphone/local-network permission.
- **Q-Link 1:** Output Gain only, -24 to +12 dB, default 0 dB. Positive gain can clip. Source selection and the single volume knob also work by touch; drag the knob vertically.
- **DIAG → VBAN Buffer:** 10–150 ms, default **120 ms for new instances**. Saved projects retain their previous setting. AirPlay has a fixed 120 ms internal prebuffer independent of this field; this does not replace its protocol buffering.
- Meter sampling targets **24 Hz**, with unchanged values suppressed. There is no refresh-rate selector. This is not a guarantee of host screen FPS.
- No AUTO mode. One active sender/source and one instance per MPC; multiple instances contend for network ports.

The physical-style skin uses one rotating grip/index image, fixed lighting and two subtle center textures. No green knob focus box or orange Q-Link bank boundary is drawn. Decoded PNG artwork is approximately 9 MiB, excluding host caches/RSS. Runtime rotation can cost more CPU than a filmstrip; repeated teeth can visually alias during fast movement.

VBAN includes jitter buffering, reordering, loss concealment, linear sample-rate conversion and a small FIFO clock correction. It is not a bandlimited converter and cannot recover arbitrary Wi-Fi outages. AirPlay requires mDNS multicast and permitted peer-to-peer traffic on the LAN. The previous iPhone album-end reconnection report is not claimed fixed.

## Build

With Docker Desktop running on macOS, or Docker on Linux:

```sh
./build.sh
./build.sh test
./build.sh airplay-test
./build.sh sanitize
```

The Debian bookworm linux/amd64 container uses arm-linux-gnueabihf-g++ and aarch64-linux-gnu-g++, builds both VSTs and bundled helpers, runs native tests, generates the skin and validates/packages the result. First build needs network access. Outputs: `build/VST2 Plugins/` and `dist/`. Blender and image generation are not build dependencies; source artwork is included.

Native tests cover parser/SPSC/SRC, UDP reordering/loss/jitter, state compatibility, fixed 24 Hz scheduling and audio while Gain changes under slow UI callbacks. Classic AirPlay PCM/encrypted ALAC loopback passed for the unchanged receiver path in 1.2.5. Version 1.3.0 changes only version metadata and the Q-Link bank outline from 1.2.5; its native/ARM builds, regression tests and skin checks passed.

Historical `tested.json` records v1.0.0 on MPC Key 61 / OS 3.10.1. User feedback also confirmed the touch fix in 1.2.4. **The final 1.3.0 bank-outline change and physical Gen2 remain unverified on hardware.** Device CPU, long sessions and all network conditions are not certified.

## Implementation and licensing

C++17 / Linux POSIX. A network worker feeds a lock-free stereo SPSC; the audio callback performs no allocation, mutex, file/socket I/O or host UI notifications. Classic AirPlay runs bundled Shairport Sync 4.3.7 with TinySVCmDNS in a child process, without Avahi/D-Bus/ALSA services or firmware changes. A private temporary helper directory is cleaned on unload; see [network/helper lifecycle](docs/NETWORK-AND-HELPER.md).

Project code is MIT. Distributed code also includes BSD-3-Clause, Apache-2.0 and LGPL-2.1-or-later components. Both helpers are byte-identical to the audited classic-only 1.1.1 builds; [licence audit](docs/LICENSE-AUDIT.json) documents disabled AirPlay-2 and convolution components. Source, notices and LGPL corresponding source are included/published. Font and CC0 icon notices remain in the repo/package; no font binaries ship in the plugin ZIP.

UID **ArLk**, plugin ID **mpcairlink** and all historical parameter IDs/order remain stable. Legacy parameters needed for saved state remain present even when their former UI controls have been removed.
