FROM debian:bookworm
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends g++ g++-arm-linux-gnueabihf g++-aarch64-linux-gnu binutils-arm-linux-gnueabihf binutils-aarch64-linux-gnu python3 python3-pil make file ca-certificates && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y --no-install-recommends fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
RUN dpkg --add-architecture armhf && dpkg --add-architecture arm64 && apt-get update && apt-get install -y --no-install-recommends autoconf automake libtool pkg-config libssl-dev libconfig-dev libpopt-dev libssl-dev:armhf libconfig-dev:armhf libpopt-dev:armhf libssl-dev:arm64 libconfig-dev:arm64 libpopt-dev:arm64 && rm -rf /var/lib/apt/lists/*
WORKDIR /work
# Source corresponding to the bundled LGPL libconfig shared library.
RUN sed -i 's/Types: deb$/Types: deb deb-src/' /etc/apt/sources.list.d/debian.sources && apt-get update && mkdir -p /opt/mpcairlink-sources && cd /opt/mpcairlink-sources && apt-get source --download-only libconfig && rm -rf /var/lib/apt/lists/*
