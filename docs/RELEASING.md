# Catalog packaging

Build with ./build.sh. For Open MPC, use tools/sdk_release.py from the
official open-mpc/mpc-vst-plugins repository. Release 1.3.0 validation used
commit 31909fd4a94e70894e0dcdbfb83e31f57b45009f.

    python3 tools/sdk_release.py SDK_PLUGIN_FOLDER --version 1.3.0 --id mpcairlink --repo sttm/mpcairlink --license 'MIT AND BSD-3-Clause AND Apache-2.0 AND LGPL-2.1-or-later' -o dist/catalog -- --requires 'MPC OS 3.10.1+; local network; one AirLink instance per MPC'
    python3 tools/catalog_check.py ZIP --catalog --expect-id mpcairlink --expect-repo sttm/mpcairlink --require-portable

Publish both per-CPU archives and the combined SDK USB ZIP, with checksums.
Check uploaded SHA256 digests and use a pinned tag/commit preview in the
catalog. Only maintainers merge catalog entries and set reviewed trust flags.
Do not claim new hardware verification from desktop tests.
