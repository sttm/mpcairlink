# Catalog checks — 2026-11-18

Open MPC tools pinned to bab404d9b169c762bf67451ea7ce2667513a1328.

- test_catalog.py: 208 tests, OK (33 skipped), Linux non-root uid 501:20.
- catalog_build.py --check-registry: 273 entries, 4 collections, zero problems.
- Both CPU ZIPs: catalog_check.py --catalog --expect-id mpcairlink
  --expect-repo sttm/mpcairlink --require-portable: exit 0.
- Expected scanner flags: network/process APIs in the plugin and helper,
  network/dlopen/exec/uid capabilities in bundled upstream libraries; ARMv7
  requires glibc 2.36, so MPC OS 3.x only. min_os remains 3.10.1.
- No flags_reviewed self-assigned; maintainer review is still required.
- No font binaries in either catalog ZIP; archive CRC checks passed.

SHA256:

```
a129120651638783875810640b859b35bb015db02dad29a71e4cd874e522a6bd  mpcairlink-1.1.1-mpc-aarch64.zip
02a729437be2412133cd45055f8bc550a063c00648c6d5cc23e428165b6c0779  mpcairlink-1.1.1-mpc-armv7.zip
1b1e82fc461c719c49536a121dea101b675f279ed36d110d6c46be1dd1dc82c0  mpcairlink-1.1.1-mpc.zip
```

See CATALOG-CHECK-armv7.json, CATALOG-CHECK-aarch64.json, BUILD-CHECKS.log,
LICENSE-AUDIT.json and NETWORK-AND-HELPER.md for details. CI/merge approval
belongs to Open MPC maintainers; local checks do not replace their review.
