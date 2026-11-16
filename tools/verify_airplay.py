#!/usr/bin/env python3
"""Check all shipped helper binaries/libraries without executing ARM code."""
import re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for arch,triplet,machine in [('arm32','arm-linux-gnueabihf','ARM'),('arm64','aarch64-linux-gnu','AArch64')]:
    helper=ROOT/'Content/AirPlay'/('shairport-sync-'+arch)
    libs=ROOT/'Content/AirPlay'/('lib-'+arch)
    allowed={'libc.so.6','libm.so.6','libpthread.so.0','libdl.so.2','librt.so.1','libgcc_s.so.1','ld-linux-armhf.so.3','ld-linux-aarch64.so.1'} | {f.name for f in libs.iterdir()}
    for f in [helper,*sorted(libs.iterdir())]:
        header=subprocess.check_output([triplet+'-readelf','-h',str(f)],text=True)
        assert re.search(r'Machine:\s+'+machine+r'\s*$',header,re.M),f
        dynamic=subprocess.check_output([triplet+'-readelf','-d',str(f)],text=True)
        needed=set(re.findall(r'Shared library: \[(.*?)\]',dynamic))
        assert needed<=allowed,(f,needed-allowed)
        versions=subprocess.check_output([triplet+'-readelf','-V',str(f)],text=True)
        required=[tuple(map(int,v.split('.'))) for v in re.findall(r'GLIBC_(\d+(?:\.\d+)+)',versions)]
        assert not required or max(required)<=(2,39),(f,max(required))
    print('PASS AirPlay',arch,'ELF architecture, dependencies resolved inside bundle/system libc, GLIBC <= 2.39')
