MPC Plugin Builder SDK: inMusic Software, MIT.
https://github.com/inmusic-software/mpc-plugin-builder-sdk
Pinned source commit: febd2ca5bd9eb16c4a412837196e145566bc981b (vendored).
Framework, clean-room VST2 ABI, UI-kit builders, validator and host simulator.
Original licence: vendor/mpc-plugin-builder-sdk/LICENSE.

Open MPC research/reference (no wrapper code copied):
https://github.com/open-mpc/mpc-vst-plugins
See docs/SDK-PORTING.md there for hardware-tested radio button and meter rules.
This is a community plugin by sttm, not an Akai-certified product.

DejaVu Sans Mono is used by tools/make_skin.py to bake captions into original PNG
artwork. DejaVu/Bitstream Vera font licence is shipped as FONT-LICENSE.txt.
No font binary is distributed or loaded on the MPC; live text uses the MPC host’s Roboto font.

VBAN is the VB-Audio network audio protocol. Parser follows revision 13:
https://vb-audio.com/Voicemeeter/VBANProtocol_Specifications.pdf
No VB-Audio implementation code is copied.


AirPlay: Shairport Sync 4.3.7, upstream commit
0b1c4391ffd398e7b145eb4b98416261380adeea (vendored in vendor/shairport-sync).
https://github.com/mikebrady/shairport-sync/tree/4.3.7
Shairport/Sync core and David Hammerton ALAC: MIT (see individual files).
TinySVCmDNS: Darell Tan, BSD 3-clause. Full notices shipped under
Content/AirPlay/Licenses. The upstream source is unmodified.

Bundled helper-only shared libraries: OpenSSL 3 (Apache-2.0), libconfig 1.5
(LGPL-2.1-or-later), libpopt 1.19 (MIT, see Debian copyright for components).
Full copyright notices / licence texts are in Content/AirPlay/Licenses.
Corresponding Debian libconfig sources (.dsc, orig tarball, Debian patch)
are in Content/AirPlay/Source. Users may replace/relink these helper
libraries and may reverse-engineer for debugging such modifications, as
per the applicable licences. VST code is not linked to these libraries.
