# MPC AirLink 1.1.1 — offline release checks, 2026-11-18

This revision changes meter drawing and timing, not VBAN/RAOP audio processing.
AirPlay remains the default; VBAN is the second public source. UID ArLk and
the first 15 parameter IDs/positions are preserved. Meter Refresh is appended.

- Each level image has 23 pre-rendered frames, containing 0–22 whole blocks.
  Two native FilmStrip images replace reveal/clipping meters; no partial block
  is produced by a horizontal fill rectangle. Static artwork is shared.
- Default meter sampling target: 24 Hz; selectable 10 Hz on DIAG.
- Independent status polling: up to 10 Hz. Touch controls use the native host.
- Immediate envelope attack, 120 ms time-based release; audio block peaks are
  accumulated until sampled by the UI. Unchanged quantized states send no event.
- Absolute meter deadlines and missed-tick dropping prevent catch-up bursts.
- Test-only instrumentation measured approximately 24 Hz and 10 Hz sampling.
  Under deliberately slow 8 ms host UI callbacks, a changing UDP signal produced
  more than ten changed meter events per second, without UI calls from the audio
  thread. These are computer measurements, not MPC compositor FPS measurements.
- Native core/network/reordering/loss, clock-drift/20-minute virtual listening,
  real PCM/ALAC AirPlay and RTSP OPTIONS after teardown checks passed.
- Host simulator's network-input silence warning is expected: MIDI notes do
  not produce audio in this receiver. No host-simulator FAIL is accepted.

The 1.1.1 screen, filmstrip frame selection and performance require a real MPC
test. If 24 Hz causes audible glitches on the device, use DIAG → 10 Hz and report
the result. Both are candidates; no guaranteed minimum physical FPS is claimed.
Album art and track-title metadata remain disabled, as in 1.1.0.

Artwork update, 2026-11-18: replaced the AirPlay button icon with the supplied
SVG geometry (screen and outlined triangle). Removed the header icon and added
original outlined AIRLINK lettering inspired by the supplied reference. These
are build-time raster assets; binaries, parameter layout and refresh rates are
unchanged. Regenerated all previews and checked the receiving screen visually.

Clean public source rebuild on 2026-11-18:
- ARMv7 hard-float and AArch64 compiled with -Wall -Wextra -Werror.
- Native parser/SPSC/SRC, jitter, 20 virtual minutes of drift/listening,
  actual UDP reorder/loss and host simulation passed (18 host checks, one
  expected silence warning, zero failures).
- Real RTSP/RTP PCM and encrypted ALAC through the VST passed.
- ASan/UBSan parser, SPSC, network, packet-queue and UDP loss tests passed.
- SDK package validation: zero errors, zero warnings.
- Meter sampling measured about 24.46 Hz and 10.00 Hz; changed meter events
  were 43 per channel over 2.32 seconds with slow host callbacks. No UI
  callbacks occurred in the audio path. These are offline observations.
- Both helper configurations exclude AirPlay 2 and convolution; 38 compiler
  dependency files per architecture omit the GPL-tagged optional parts.
  See LICENSE-AUDIT.json and NETWORK-AND-HELPER.md.

Physical testing remains v1.0.0 on Key 61 / OS 3.10.1 (2026-11-16).
The iPhone reconnect problem after album-end has no confirmed device fix;
only a fresh RTSP OPTIONS request after teardown is covered by automated tests.
