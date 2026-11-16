#!/bin/sh
# Build classic AirPlay helper without Avahi, D-Bus, ALSA or system services.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"
if [ ! -f build/airplay-source/configure ]; then
  mkdir -p build/airplay-source
  cp -R vendor/shairport-sync/. build/airplay-source/
  (cd build/airplay-source && autoreconf -fi)
fi
for target in native arm32 arm64; do
  case "$target" in
    native) host=x86_64-linux-gnu; archflags=;;
    arm32) host=arm-linux-gnueabihf; archflags='-march=armv7-a -mfpu=neon-vfpv4 -mfloat-abi=hard';;
    arm64) host=aarch64-linux-gnu; archflags='-march=armv8-a';;
  esac
  dest="build/airplay-$target"
  mkdir -p "$dest"
  if [ ! -f "$dest/Makefile" ]; then
    (cd "$dest" && CC="$host-gcc" CXX="$host-g++" AR="$host-ar" RANLIB="$host-ranlib" \
      CFLAGS="-O2 $archflags" LDFLAGS='-Wl,--as-needed' \
      ../airplay-source/configure --host="$host" --with-stdout --with-ssl=openssl \
      --with-tinysvcmdns --without-pkg-config --without-configfiles --without-libdaemon \
      > configure.log 2>&1) || { cat "$dest/configure.log"; exit 1; }
  fi
  make -C "$dest" -j4 > "$dest/build.log" 2>&1 || { tail -100 "$dest/build.log"; exit 1; }
  mkdir -p Content/AirPlay
  "$host-strip" "$dest/shairport-sync" -o "Content/AirPlay/shairport-sync-$target"
  mkdir -p "Content/AirPlay/lib-$target"
  for lib in libssl.so.3 libcrypto.so.3 libpopt.so.0 libconfig.so.9; do
    cp -L "/usr/lib/$host/$lib" "Content/AirPlay/lib-$target/$lib"
  done
  file "Content/AirPlay/shairport-sync-$target"
done

mkdir -p Content/AirPlay/Licenses Content/AirPlay/Source
cp /opt/mpcairlink-sources/* Content/AirPlay/Source/
for lib in libssl-dev libconfig-dev libpopt-dev; do
  cp "/usr/share/doc/$lib/copyright" "Content/AirPlay/Licenses/$lib-copyright.txt"
done
for license in LGPL-2.1 GPL-2 GPL-3 Apache-2.0; do
  cp "/usr/share/common-licenses/$license" "Content/AirPlay/Licenses/$license.txt"
done
cp vendor/shairport-sync/LICENSES Content/AirPlay/Licenses/Shairport-Sync.txt
cp vendor/shairport-sync/alac.c Content/AirPlay/Licenses/alac.c
cp vendor/shairport-sync/tinysvcmdns.h Content/AirPlay/Licenses/tinysvcmdns.h
