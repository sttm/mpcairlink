# Catalog checks — 1.3.0

Official catalog tools at 31909fd4a94e70894e0dcdbfb83e31f57b45009f.
218 catalog tests passed (33 skipped), registry 304 entries / 6 collections /
0 problems. SDK validator: 0 errors, 0 warnings. Clean ARMv7/AArch64 and native
build, core/UDP/jitter/loss/state/UI tests, PCM/encrypted ALAC, ASan/UBSan passed.

Capabilities below are intentionally disclosed and unchanged in purpose:
network reception and spawning bundled classic Shairport; helper libraries
retain upstream exported network/dlopen/hook/privilege symbols. AirLink config
does not enable arbitrary hooks or privilege changes. These are scanner
capability findings, not self-approved trust flags. Only maintainers may set
flags_reviewed; this update does not alter it or catalog policy/trust files.
ARMv7 GLIBC 2.36 requires MPC OS 3.x; min_os stays 3.10.1.

The final 1.3.0 skin and Gen2 remain offline-only pending hardware feedback.
Historical device evidence is not promoted to a new-version claim.

## armv7

PASS catalog_check --catalog --require-portable (exit 0).

SHA256: `30de69be784601133ed16c32b7cb78b54cb49274a85e8ac5cc737e733dcf828f`; size 6337471 bytes.

```text
warning: needs GLIBC 2.36: listed as MPC OS 3.x only (MPC OS 2.x has about 2.32; build with arm32v7/gcc:11-bullseye to reach it)
warning: portable/sttm - VST - MPC AirLink/Content/AirPlay/lib-arm32/libcrypto.so.3 calls network (accept, bind, connect, getaddrinfo, gethostbyname, listen, recvfrom, sendto, socket); loads code at runtime (dlopen): flagged for manual review (the author can explain why)
warning: portable/sttm - VST - MPC AirLink/Content/AirPlay/lib-arm32/libpopt.so.0 calls runs programs (execvp); changes the system (setgid, setuid): flagged for manual review (the author can explain why)
warning: portable/sttm - VST - MPC AirLink/Content/AirPlay/lib-arm64/libcrypto.so.3 calls network (accept, bind, connect, getaddrinfo, gethostbyname, listen, recvfrom, sendto, socket); loads code at runtime (dlopen): flagged for manual review (the author can explain why)
warning: portable/sttm - VST - MPC AirLink/Content/AirPlay/lib-arm64/libpopt.so.0 calls runs programs (execvp); changes the system (setgid, setuid): flagged for manual review (the author can explain why)
warning: portable/sttm - VST - MPC AirLink/Content/AirPlay/shairport-sync-arm32 calls network (accept, bind, getaddrinfo, listen, recv, recvfrom, sendto, socket); runs programs (execv, fork, popen): flagged for manual review (the author can explain why)
warning: portable/sttm - VST - MPC AirLink/Content/AirPlay/shairport-sync-arm64 calls network (accept, bind, getaddrinfo, listen, recv, recvfrom, sendto, socket); runs programs (execv, fork, popen): flagged for manual review (the author can explain why)
warning: portable/sttm - VST - MPC AirLink/VST/mpcairlink-arm32.so calls network (bind, recvfrom, socket); runs programs (posix_spawn): flagged for manual review (the author can explain why)
```

## aarch64

PASS catalog_check --catalog --require-portable (exit 0).

SHA256: `6274030a89de78a9aafa60f2fb7723c8b36866cd826eaed3e0ad262f695a8fe4`; size 6364692 bytes.

```text
warning: portable/sttm - VST - MPC AirLink/Content/AirPlay/lib-arm32/libcrypto.so.3 calls network (accept, bind, connect, getaddrinfo, gethostbyname, listen, recvfrom, sendto, socket); loads code at runtime (dlopen): flagged for manual review (the author can explain why)
warning: portable/sttm - VST - MPC AirLink/Content/AirPlay/lib-arm32/libpopt.so.0 calls runs programs (execvp); changes the system (setgid, setuid): flagged for manual review (the author can explain why)
warning: portable/sttm - VST - MPC AirLink/Content/AirPlay/lib-arm64/libcrypto.so.3 calls network (accept, bind, connect, getaddrinfo, gethostbyname, listen, recvfrom, sendto, socket); loads code at runtime (dlopen): flagged for manual review (the author can explain why)
warning: portable/sttm - VST - MPC AirLink/Content/AirPlay/lib-arm64/libpopt.so.0 calls runs programs (execvp); changes the system (setgid, setuid): flagged for manual review (the author can explain why)
warning: portable/sttm - VST - MPC AirLink/Content/AirPlay/shairport-sync-arm32 calls network (accept, bind, getaddrinfo, listen, recv, recvfrom, sendto, socket); runs programs (execv, fork, popen): flagged for manual review (the author can explain why)
warning: portable/sttm - VST - MPC AirLink/Content/AirPlay/shairport-sync-arm64 calls network (accept, bind, getaddrinfo, listen, recv, recvfrom, sendto, socket); runs programs (execv, fork, popen): flagged for manual review (the author can explain why)
warning: portable/sttm - VST - MPC AirLink/VST/mpcairlink-arm64.so calls network (bind, recvfrom, socket); runs programs (posix_spawn): flagged for manual review (the author can explain why)
```
