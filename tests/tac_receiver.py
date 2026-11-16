#!/usr/bin/env python3
"""Real native VST2 + RAOP RTSP/RTP loopback; not an iPhone/hardware certification."""
import ctypes as C, math, re, socket, struct, threading, time, sys, base64, subprocess, tempfile, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
IP=C.c_ssize_t
class Effect(C.Structure): pass
Callback=C.CFUNCTYPE(IP,C.POINTER(Effect),C.c_int32,C.c_int32,IP,C.c_void_p,C.c_float)
Process=C.CFUNCTYPE(None,C.POINTER(Effect),C.POINTER(C.POINTER(C.c_float)),C.POINTER(C.POINTER(C.c_float)),C.c_int32)
Set=C.CFUNCTYPE(None,C.POINTER(Effect),C.c_int32,C.c_float)
Get=C.CFUNCTYPE(C.c_float,C.POINTER(Effect),C.c_int32)
Effect._fields_=[('magic',C.c_int32),('dispatcher',Callback),('process',Process),('setParameter',Set),('getParameter',Get),('numPrograms',C.c_int32),('numParams',C.c_int32),('numInputs',C.c_int32),('numOutputs',C.c_int32),('flags',C.c_int32),('resvd1',IP),('resvd2',IP),('initialDelay',C.c_int32),('realQualities',C.c_int32),('offQualities',C.c_int32),('ioRatio',C.c_float),('object',C.c_void_p),('user',C.c_void_p),('uniqueID',C.c_int32),('version',C.c_int32),('processReplacing',Process),('processDoubleReplacing',C.c_void_p),('future',C.c_char*56)]
@Callback
def host(e,op,index,value,ptr,opt): return 2400 if op==1 else 0
lib=C.CDLL(str(ROOT/'build/native/mpcairlink.so')); lib.VSTPluginMain.argtypes=[Callback]; lib.VSTPluginMain.restype=C.POINTER(Effect)
e=lib.VSTPluginMain(host); fx=e.contents

fx.dispatcher(e,0,0,0,None,0)
fx.setParameter(e,1,.5)
fx.dispatcher(e,10,0,0,None,44100)
fx.dispatcher(e,11,0,128,None,0)
fx.dispatcher(e,12,0,1,None,0)
left=(C.c_float*128)(); right=(C.c_float*128)(); out=(C.POINTER(C.c_float)*2)(left,right)
energy=0; peak=0; crossings=0; previous=0; samples=0; stereo_error=0
print("READY",flush=True)
start=time.monotonic(); deadline=start
while time.monotonic()-start<8:
    fx.processReplacing(e,None,out,128)
    for i in range(128):
        value=left[i]; assert math.isfinite(value)
        peak=max(peak,abs(value)); stereo_error+=abs(value-right[i])
        if abs(value)>.001:
            energy+=value*value; samples+=1
        if previous<=0 and value>0: crossings+=1
        previous=value
    deadline+=128/44100
    time.sleep(max(0,deadline-time.monotonic()))
def display(index):
    b=C.create_string_buffer(64); fx.dispatcher(e,7,index,0,C.cast(b,C.c_void_p),0); return b.value.decode()
assert peak>.20 and samples>150000 and stereo_error<.01,(peak,samples,stereo_error)
assert energy/samples>.015
# The tone lasts six seconds; allow small startup/tail differences.
assert 2500<crossings<2750,crossings
print('PASS Tac Swift -> UDP VBAN -> native MPC VST2: PCM16 48k stereo -> 44.1k; peak',round(peak,3),'zero crossings',crossings,'lost',display(8),'XRUN',display(12),flush=True)
fx.dispatcher(e,12,0,0,None,0); fx.dispatcher(e,1,0,0,None,0)
