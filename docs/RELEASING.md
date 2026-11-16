# Catalog packaging

Build and test with `./build.sh` first. The combined USB archive is emitted into `dist/`.
For Open MPC, use the official SDK bridge from a separate checkout:

```sh
git clone https://github.com/open-mpc/mpc-vst-plugins.git /tmp/open-mpc-release
git -C /tmp/open-mpc-release checkout 932ad3149f2c368ae1d4d422614f8b20c075622e
python3 /tmp/open-mpc-release/tools/sdk_release.py \
  'build/VST2 Plugins/sttm - VST - MPC AirLink' \
  --version 1.0.0 --id mpcairlink --repo sttm/mpcairlink \
  --license 'MIT AND BSD-3-Clause AND Apache-2.0 AND LGPL-2.1-or-later AND Bitstream-Vera' \
  -o dist/catalog -- --requires 'MPC OS 3.10.1+; local network; one AirLink instance per MPC'
python3 /tmp/open-mpc-release/tools/catalog_check.py \
  dist/catalog/MPC-AirLink-1.0.0-mpc-armv7.zip --catalog --expect-id mpcairlink --expect-repo sttm/mpcairlink --require-portable
python3 /tmp/open-mpc-release/tools/catalog_check.py \
  dist/catalog/MPC-AirLink-1.0.0-mpc-aarch64.zip --catalog --expect-id mpcairlink --expect-repo sttm/mpcairlink --require-portable
```

Run the catalog tools on Linux for their full test suite. Review expected warnings in [NETWORK-AND-HELPER.md](NETWORK-AND-HELPER.md). Keep hardware claims in tested.json precise; do not add Gen2 until an actual device test. The registry needs min_os 3.10.1 and a pinned image URL. Only maintainers set flags_reviewed.
