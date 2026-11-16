#!/usr/bin/env python3
"""Real native VST2 + RAOP RTSP/RTP loopback; not an iPhone/hardware certification."""
import os
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
def host(e,op,index,value,ptr,opt):
    if op==0 and os.getenv('MPC_TEST_SLOW_HOST')=='1': time.sleep(.008)
    return 2400 if op==1 else 0
lib=C.CDLL(str(ROOT/'build/native/mpcairlink.so')); lib.VSTPluginMain.argtypes=[Callback]; lib.VSTPluginMain.restype=C.POINTER(Effect)
e=lib.VSTPluginMain(host); fx=e.contents

def dispatch(op,index=0,value=0,ptr=None,opt=0): return fx.dispatcher(e,op,index,value,ptr,opt)
def display(index):
    b=C.create_string_buffer(64); dispatch(7,index,ptr=C.cast(b,C.c_void_p)); return b.value.decode()

def ntp():
    t=time.time()+2208988800; sec=int(t); return (sec<<32)|int((t-sec)*2**32)

def udp():
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.bind(('127.0.0.1',0)); s.settimeout(.1); return s

# Subscribe before loading so startup DNS-SD announcements are observable.
mdns=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); mdns.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1); mdns.bind(('',5353)); mdns.setsockopt(socket.IPPROTO_IP,socket.IP_ADD_MEMBERSHIP,socket.inet_aton('224.0.0.251')+socket.inet_aton('0.0.0.0')); mdns.settimeout(.1)
dispatch(0); dispatch(10,opt=44100); dispatch(11,value=128); fx.setParameter(e,1,1); dispatch(12,value=1)
rtsp=None; alive=True; rendered=[]; audio_thread=None; timer_thread=None; stereo_error=[0.0]
try:
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        try: rtsp=socket.create_connection(('127.0.0.1',5000),.1); break
        except OSError: time.sleep(.05)
    assert rtsp is not None, 'AirPlay helper did not start: '+display(13)
    rtsp.settimeout(3); seq=0; session=''
    def request(method,headers=None,body=b''):
        global seq,session
        seq+=1
        data=f'{method} rtsp://127.0.0.1/stream RTSP/1.0\r\nCSeq: {seq}\r\nUser-Agent: AirLinkTest/1.0\r\nX-Apple-Client-Name: Loopback\r\n'
        if session: data+='Session: '+session+'\r\n'
        for k,v in (headers or {}).items(): data+=f'{k}: {v}\r\n'
        if body: data+=f'Content-Length: {len(body)}\r\n'
        rtsp.sendall(data.encode()+b'\r\n'+body)
        response=b''
        while b'\r\n\r\n' not in response: response+=rtsp.recv(8192)
        assert response.startswith(b'RTSP/1.0 200'),response
        h=dict(line.split(': ',1) for line in response.decode().split('\r\n')[1:] if ': ' in line)
        if 'Session' in h: session=h['Session']
        return h
    h=request('OPTIONS',{'Apple-Challenge':'AAECAwQFBgcICQoLDA0ODw=='})
    assert 'Apple-Response' in h,'Missing RSA AirPlay challenge response'
    encrypted='--alac' in sys.argv
    aeskey=bytes(range(16)); aesiv=bytes(range(16,32))
    if encrypted:
        # Public key is derived from Shairport's published protocol key; it is not a user secret.
        source=(ROOT/'vendor/shairport-sync/common.c').read_text()
        block=source.split('static char super_secret_key[] =',1)[1].split(';',1)[0]
        pem=''.join(json.loads(line.strip().replace(r"\0",r"\n")) for line in block.splitlines() if line.strip().startswith('"')).encode()
        with tempfile.TemporaryDirectory() as tmp:
            pub=Path(tmp)/'raop-public.pem'
            pub.write_bytes(subprocess.run(['openssl','pkey','-pubout'],input=pem,capture_output=True,check=True).stdout)
            wrapped=subprocess.run(['openssl','pkeyutl','-encrypt','-pubin','-inkey',str(pub),'-pkeyopt','rsa_padding_mode:oaep'],input=aeskey,capture_output=True,check=True).stdout
        crypto=C.CDLL('libcrypto.so.3')
        key_schedule=C.create_string_buffer(256)
        crypto.AES_set_encrypt_key.argtypes=[C.c_void_p,C.c_int,C.c_void_p]
        crypto.AES_cbc_encrypt.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_int]
        assert crypto.AES_set_encrypt_key(aeskey,128,key_schedule)==0
    sdp=b'v=0\r\no=iTunes 1 0 IN IP4 127.0.0.1\r\ns=AirLinkTest\r\nc=IN IP4 127.0.0.1\r\nt=0 0\r\nm=audio 0 RTP/AVP 96\r\na=rtpmap:96 L16/44100/2\r\n'
    if encrypted:
        sdp=sdp.replace(b'a=rtpmap:96 L16/44100/2',b'a=rtpmap:96 AppleLossless')
        sdp+=b'a=fmtp:96 352 0 16 40 10 14 2 255 0 0 44100\r\n'
        sdp+=b'a=rsaaeskey:'+base64.b64encode(wrapped)+b'\r\na=aesiv:'+base64.b64encode(aesiv)+b'\r\n'
    request('ANNOUNCE',{'Content-Type':'application/sdp'},sdp)
    timing=udp(); control=udp(); audio=udp()
    h=request('SETUP',{'Transport':f'RTP/AVP/UDP;unicast;mode=record;control_port={control.getsockname()[1]};timing_port={timing.getsockname()[1]}'})
    ports=dict(re.findall(r'(server_port|control_port|timing_port)=(\d+)',h['Transport']))
    def timing_loop():
        while alive:
            try:
                data,addr=timing.recvfrom(2048)
                if len(data)>=32 and data[1]==0xd2:
                    now=ntp(); reply=struct.pack('!BBHIQQQ',0x80,0xd3,7,0,struct.unpack('!Q',data[24:32])[0],now,ntp()); timing.sendto(reply,addr)
            except socket.timeout: pass
    timer_thread=threading.Thread(target=timing_loop); timer_thread.start()
    stamp=882000
    request('RECORD',{'Range':'npt=0-','RTP-Info':f'seq=1;rtptime={stamp}'})
    request('SET_PARAMETER',{'Content-Type':'text/parameters'},b'volume: 0.0\r\n')
    def render():
        left=(C.c_float*128)(); right=(C.c_float*128)(); out=(C.POINTER(C.c_float)*2)(left,right); end=time.monotonic()
        while alive:
            fx.processReplacing(e,None,out,128); rendered.extend(left); stereo_error[0]+=sum(abs(left[i]+right[i]) for i in range(128)); end+=128/44100; time.sleep(max(0,end-time.monotonic()))
    audio_thread=threading.Thread(target=render); audio_thread.start()
    start=time.monotonic(); discovered=False; vban=udp()
    for packet in range(750):
        ts=stamp+packet*352
        if packet==400: fx.setParameter(e,1,0) # AUTO keeps an already-playing AirPlay source.
        if packet>=400:
            vp=struct.pack('<4sBBBB16sI',b'VBAN',3,127,1,1,b'Stream1',packet)+struct.pack('<256h',*([28000]*256))
            vban.sendto(vp,('127.0.0.1',6980))
        # Audio timestamp is current send time; the playback target includes sender latency.
        if packet%20==0:
            query=struct.pack('!6H',0,0,1,0,0,0)+b'\x05_raop\x04_tcp\x05local\0'+struct.pack('!HH',12,1)
            mdns.sendto(query,('224.0.0.251',5353))
            sync=struct.pack('!BBHIQI',0x80,0xd4,4,(ts-88200)&0xffffffff,ntp(),ts)
            control.sendto(sync,('127.0.0.1',int(ports['control_port'])))
        samples=[]
        for i in range(352):
            v=int(14000*math.sin(2*math.pi*440*(packet*352+i)/44100)); samples.extend([v,-v])
        if encrypted:
            bits='001'+'0'*16+'0'+'00'+'1'+''.join(f'{v&65535:016b}' for v in samples)+'111'
            bits+='0'*(-len(bits)%8)
            raw=int(bits,2).to_bytes(len(bits)//8,'big')
            n=len(raw)//16*16; ciphertext=C.create_string_buffer(n); iv=C.create_string_buffer(aesiv)
            crypto.AES_cbc_encrypt(raw,ciphertext,n,key_schedule,iv,1)
            body=ciphertext.raw+raw[n:]
        else: body=struct.pack('!704h',*samples)
        payload=struct.pack('!BBHII',0x80,0x60,(packet+1)&65535,ts,1)+body
        audio.sendto(payload,('127.0.0.1',int(ports['server_port'])))
        if not discovered:
            mdns.setblocking(False)
            try:
                data=mdns.recv(9000); discovered=b'_raop' in data and b'MPC AirLink' in data
            except BlockingIOError: pass
        time.sleep(max(0,start+(packet+1)*352/44100-time.monotonic()))
    print('AirPlay status:',display(13),'connection:',display(5),'source:',display(6),flush=True)
    request('TEARDOWN')
    assert max(map(abs,rendered),default=0)>.05,'No PCM from RAOP reached VST output'
    assert display(6)=='AirPlay',display(6)
    assert stereo_error[0]<max(1,len(rendered))*0.001,'AUTO mixed VBAN into the active AirPlay source'
    assert discovered,'DNS-SD RAOP announcement not observed'
    # AirPlay Only must reject VBAN; after switching, the listener must stop.
    fx.setParameter(e,1,.5); time.sleep(.5)
    assert display(13).startswith(('O','H')),display(13) # VBAN diagnostics replace the disabled label.
    try:
        probe=socket.create_connection(('127.0.0.1',5000),.1); probe.close(); raise AssertionError('AirPlay listener remained in VBAN Only')
    except (ConnectionRefusedError,socket.timeout): pass
    print(('Encrypted ALAC: ' if encrypted else 'PCM: ')+ 'PASS real VST2 AirPlay: mDNS discovery, RTSP OPTIONS/ANNOUNCE/SETUP/RECORD, NTP/RTP PCM audio, source status, VBAN Only stops service',flush=True)
finally:
    alive=False
    if audio_thread: audio_thread.join()
    if timer_thread: timer_thread.join()
    for name in ("vban","audio","control","timing"):
        sock=globals().get(name)
        if sock is not None: sock.close()
    if rtsp: rtsp.close()
    mdns.close(); dispatch(12,value=0); dispatch(1)
