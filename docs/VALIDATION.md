# MPC AirLink 1.3.0 — listening controls

MPC OS 3.10.1+ with External Plugin Support. Same mpcairlink / sttm / ArLk
identity and all 18 parameter IDs/order. ARMv7 hard-float and AArch64 builds.

STREAM now has one physical Output knob. Q-Link 1 maps only to Gain (index 3)
on both STREAM and DIAG and in Program Mode; all other Q-Link entries are -1.
Source uses touch buttons. VBAN Buffer (index 2) is moved to a 220x48 touch
field on DIAG. A transparent native FilmStrip above its value label accepts
vertical dragging; its actions do not request Q-Link reassignment on touch.
The physical Output retains the working 1.2.4 topmost transparent touch control,
one rotating grip/index image, fixed light, and no rectangular Focus overlay.

New instances default to 120 ms VBAN Buffer, adjustable 10..150 ms in DIAG.
Stored projects retain their existing saved latency. AirPlay internal
prebuffer is fixed at 120 ms independent of the VBAN field, including old
saved values above 120. This does not alter AirPlay protocol latency or
guarantee recovery from arbitrary network outages. The buffer-policy core
test checks AirPlay independence across the full VBAN range.

Meter scheduling is fixed to a target 24 Hz; the 10/24 controls and textures
are removed. Legacy parameter 15 retains ID/choices/default for saved state,
is nonautomatable and has no scheduling effect. The slow-host test verifies
24 Hz with either legacy parameter value, no idle notifications, and UDP
audio during Gain changes. Phase parameter 16 is now inert; 17 updates
Output texture only after movement from the display worker.

Installed artwork is approximately 9 MiB decoded RGBA by PNG dimensions,
excluding runtime caches and full RSS. This is not a hardware CPU benchmark.
No networking, I/O, locks, allocations or UI callbacks were added to process().
The AirPlay threshold policy is the only audio-path change. VBAN buffering
and source locking, resampling and gain smoothing algorithms are unchanged.

Checks: build/airlink-1.3.0-checks.log (cross/native builds, core/UDP/jitter/
loss/state/slow-host tests, host simulator, PCM and encrypted ALAC AirPlay
loopback, skin contract and package validator). The generic host simulator
warns of silence because it has no network sender; audio is checked separately.
Integrity: build/airlink-1.3.0-integrity.log.

Hardware follow-up: confirm Q-Link 1 remains volume on both tabs, Output and
DIAG Buffer finger gestures, saved project restoration, AirPlay/VBAN listening
and uninterrupted sound during continuous Output movement. Prior 1.2.4
package is retained as a fallback. No hardware certification is claimed.

1.3.0 removes hardware Q-Link bank bounds (qlinkBoundsData is empty on both tabs). Program and Screen Mode Q-Link 1 still map to Gain. Audio/network behavior is unchanged from 1.2.5; AirPlay integration results remain those of 1.2.5.
