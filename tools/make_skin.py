#!/usr/bin/env python3
"""Generate the MPC AirLink native terminal skin, Q-Links and previews."""
from pathlib import Path
import sys, math
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor/mpc-plugin-builder-sdk/tools'))
import gen_ui as ui
O=ui.obj
OUT=ROOT/'design/terminal-v1'; SKIN=ROOT/'skins'
import shutil
if SKIN.exists(): shutil.rmtree(SKIN)
SKIN.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
BG='#0b100d'; PANEL='#101a13'; LINE='#304332'; GREEN='#8fe07a'; WHITE='#e3eadf'; MUTED='#8b9b8d'; DIM='#506954'
mono='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
bold='/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'
if not Path(mono).exists():
    mono='/System/Library/Fonts/Menlo.ttc'; bold=mono
sans='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
if not Path(sans).exists(): sans='/System/Library/Fonts/Supplemental/Arial.ttf'
def font(size,weight=False,live=False): return ImageFont.truetype(sans if live else bold if weight else mono,size)
def text(draw,xy,label,size=18,color=MUTED,weight=False,anchor=None,live=False):
    draw.text(xy,label,font=font(size,weight,live),fill=color,anchor=anchor)
def rule(draw,xy,color=LINE): draw.line(xy,fill=color,width=1)
def box(draw,xy): draw.rectangle(xy,outline=LINE,fill=PANEL,width=1)
panel=Image.new('RGB',(1280,628),BG); d=ImageDraw.Draw(panel)
# A terminal window, with clear hierarchy and touch-sized controls.
text(d,(40,25),'>_',30,GREEN,True)
text(d,(92,25),'MPC AIRLINK',30,WHITE,True)
text(d,(1240,40),'sttm / NETWORK AUDIO',16,MUTED,anchor='rm')
rule(d,(40,78,1240,78))
box(d,(40,100,785,233)); box(d,(805,100,1240,233))
text(d,(60,114),'LISTEN ADDRESS',17)
text(d,(60,203),'UDP 6980   /   VBAN: ANY STREAM',16,DIM)
text(d,(825,114),'CONNECTION',17)
# A tiny permanent ANY label replaces the entire filter control section.
text(d,(40,253),'INPUT SOURCE',17)
text(d,(1240,253),'FIRST ACTIVE SOURCE WINS',15,DIM,anchor='ra')
for x,title in [(40,'AUTO'),(450,'VBAN Only'),(860,'AirPlay Only')]:
    for on in (False,True):
        im=Image.new('RGB',(380,64),GREEN if on else BG); b=ImageDraw.Draw(im)
        b.rectangle((0,0,379,63),outline=GREEN if on else LINE,width=1)
        text(b,(190,32),'[ '+title.upper()+' ]',21,BG if on else WHITE,True,'mm')
        im.save(SKIN/(title.replace(' ','_')+('_on.png' if on else '_off.png')))
# Telemetry rail.
rule(d,(40,365,1240,365));rule(d,(40,444,1240,444))
for x in (410,965): rule(d,(x,380,x,430))
text(d,(40,379),'STREAM',15,DIM); text(d,(435,379),'FORMAT',15,DIM); text(d,(990,379),'NETWORK',15,DIM)
# Large flat faders, values above the touch rail.
box(d,(40,465,420,581));box(d,(440,465,820,581));box(d,(840,465,1240,581))
text(d,(60,476),'JITTER BUFFER',17);text(d,(460,476),'OUTPUT GAIN',17)
text(d,(860,476),'STEREO LEVEL',17)
text(d,(860,511),'L',17,GREEN);text(d,(860,543),'R',17,GREEN)
rule(d,(40,602,1240,602))
text(d,(40,611),'VBAN + AIRPLAY AUDIO',12,DIM)
text(d,(1240,611),'sttm / MPC AIRLINK',12,DIM,anchor='ra')
panel.save(SKIN/'terminal-panel.png')
# 336 x 58 touch surface; native Knob filmstrip gives Q-Link and drag support.
frames=127; w,h=336,58
strip=Image.new('RGB',(w,h*frames),PANEL); sd=ImageDraw.Draw(strip)
for frame in range(frames):
    y=frame*h; pos=12+int(frame/(frames-1)*(w-24))
    rule(sd,(12,y+30,w-12,y+30),DIM)
    rule(sd,(12,y+30,pos,y+30),GREEN)
    for i in range(9):
        x=12+int(i*(w-24)/8); rule(sd,(x,y+38,x,y+41),LINE)
    sd.rectangle((pos-3,y+18,pos+3,y+41),fill=GREEN)
strip.save(SKIN/'terminal-slider.png')
for state in ('off','on'):
    im=Image.new('RGB',(330,20),PANEL); md=ImageDraw.Draw(im)
    for i in range(22):
        md.rectangle((i*15,2,i*15+10,17),fill=(GREEN if i<18 else '#d2cf76' if i<21 else '#e88578') if state=='on' else '#263a2b')
    im.save(SKIN/('terminal-meter-'+state+'.png'))
E=ui.entry

def entry(name,typ,data,bounds,param=None,focus='No'):
    return E(name,typ,data,bounds,focus,'Show','Always',remap=[] if param is None else [('Data',f'Parameter {param}')])
children=[entry('terminal panel','Image',O(('version',2),('imageType','Regular'),('colour','00000000'),('image','terminal-panel.png')),'0 0 1280 628')]

def label(name,p,bounds,height=32,color='ffe3eadf',right=False):
    data=ui.label_data('Value',color,height,'right verticallyCentred' if right else 'left verticallyCentred')
    # Roboto is provided by MPC; all fixed text is baked in an OFL/Bitstream mono font.
    for key,value in data:
        if key=='textStyle':
            for k,v in value:
                if k=='font':
                    for i,(fk,fv) in enumerate(v):
                        if fk=='name': v[i]=(fk,'Roboto')
    children.append(entry(name,'Label',data,bounds,p))
label('address',4,'60 145 705 51',42)
label('connection',5,'825 151 390 49',38,'ff8fe07a')
label('stream',6,'40 403 350 32',30)
label('format',7,'435 403 510 32',30)
label('lost',8,'990 403 250 32',30)
for n,title in enumerate(('AUTO','VBAN Only','AirPlay Only')):
    fn=title.replace(' ','_')
    children.append(entry(title,'Button',ui.button_data(fn+'_on.png',fn+'_off.png',n,3),f'{40+n*410} 285 380 64',1))
# Flat faders retain the SDK's standard focus and large value editing overlay.
style=dict(ui.DEFAULT_STYLE,background='ff0b100d',accent='ff8fe07a',text='ffe3eadf',muted='ff8b9b8d')
slider=ui.component_definition(ui.control_actions('terminal editor'),[
    entry('focus','Focus',ui.focus_data('ff8fe07a'),'0 0 380 116'),
    entry('rail','Knob',ui.knob_filmstrip_data('terminal-slider.png',127,'Horizontal'),'20 55 336 58')
],'00000000')
# Focus ring should only appear when selected.
for key,value in slider:
    if key=='componentsData':
        focus_entry=value[0]
        for k,v in focus_entry:
            if k=='bounds':
                for i,(bk,bv) in enumerate(v):
                    if bk=='whenVisible': v[i]=(bk,'WhenFocussed')
for p,x,name in [(2,40,'latency'),(3,440,'gain')]:
    children.append(entry(name,'terminal fader',O(('version',1),('handleName','Data')),f'{x} 465 380 116',p,'Yes'))
    label(name+' value',p,f'{x+220} 471 138 43',34,'ff8fe07a',True)
for p,y in ((9,509),(10,541)):
    handle=f'Parameter {p}'
    children.append(entry('level '+str(p),'Meter',O(('version',3),('direction','Right'),('invert',False),('inactiveImage','terminal-meter-off.png'),('peakImage','terminal-meter-on.png'),('rmsImage','terminal-meter-on.png'),('peakHandle',handle),('rmsHandle',handle),('peakHoldHandle','Hold/'+handle),('peakHoldSize',2),('peakHoldColour','ffe3eadf')),f'890 {y} 330 20'))
# Diagnostics stays off the main performance page.
main_children=children
page=Image.new('RGB',(1280,628),BG); dd=ImageDraw.Draw(page)
text(dd,(40,25),'>_ AIRLINK DIAGNOSTICS',30,WHITE,True)
text(dd,(1240,40),'sttm / MPC AIRLINK',16,MUTED,anchor='rm');rule(dd,(40,78,1240,78))
for bounds,title in [((40,104,420,230),'PACKETS LOST'),((440,104,820,230),'AUDIO DROPPED'),((840,104,1240,230),'UNDERRUNS'),((40,252,1240,366),'SERVICE / BUFFER'),((40,388,620,500),'ACTIVE STREAM'),((640,388,1240,500),'AUDIO FORMAT')]:
    box(dd,bounds);text(dd,(bounds[0]+20,bounds[1]+16),title,17)
text(dd,(40,538),'O = FIFO OVERFLOW   T = BACKLOG TRIM   R = HOST RESET',16,DIM)
text(dd,(40,567),'Q = BUFFER (ms)     H = HOST RATE      C = CALLBACK RATE',16,DIM)
page.save(SKIN/'terminal-diagnostics.png')
children=[entry('diagnostics panel','Image',O(('version',2),('imageType','Regular'),('colour','00000000'),('image','terminal-diagnostics.png')),'0 0 1280 628')]
for name,param,bounds in [('lost packets',8,'60 151 340 55'),('dropped frames',11,'460 151 340 55'),('underruns',12,'860 151 360 55'),('service',13,'60 298 1160 47'),('active stream',6,'60 432 540 48'),('audio format',7,'660 432 560 48')]:
    label(name,param,bounds,36,'ff8fe07a')
diag_children=children
children=main_children

defs=[('terminal fader',slider),('terminal editor',ui.overlay_component('KnobOverlay',ui.knob_overlay_data(False),'ff0b100d'))]
tabs=[]
for index,name,items,bounds in [(0,'STREAM',main_children,['40 245 1200 336']),(1,'DIAG',diag_children,[])]:
    tabs.append(O(('version',1),('tabName',name),('fnKeyIndex',index),('fnKeySubIndex',0),('componentDefinition',ui.component_definition([],items,'ff0b100d')),('qlinkBoundsData',bounds)))
tui=O(('pageData',O(('version',1),('componentDefinitions',O(('version',2),('importFiles',[]),('localComponentDefinitions',[O(('key',k),('value',v)) for k,v in defs]))),('replacementStrings',[]),('info',O(('version',1),('type','CompleteDescription'))),('tabs',tabs))))
qmap=O(*[(f'Q-Link {q}',{1:1,2:2,3:3}.get(q,-1)) for q in range(1,17)])
none=O(*[(f'Q-Link {q}',-1) for q in range(1,17)])
maps=[O(('Tab',1),('SubTab',1),('Bank Direction','Row'),('Q-Links',qmap)),O(('Tab',2),('SubTab',1),('Bank Direction','Row'),('Q-Links',none))]
ql=O(('version',4),('info',O(('version',1),('type','CompleteDescription'))),('Screen Mode Q-Links',O(('version',4),('map',maps))),('Program Mode Q-Links',qmap))
(SKIN/'TUI.json').write_text(ui.dump_json(tui)+'\n');(SKIN/'Q-Links.json').write_text(ui.dump_json(ql)+'\n')
for state in ('receiving','waiting'):
    preview=panel.copy(); pd=ImageDraw.Draw(preview)
    active=state=='receiving'
    text(pd,(60,149),'192.0.2.10 : 6980',34,WHITE,live=True)
    text(pd,(825,154),'RECEIVING' if active else 'WAITING _',32,GREEN if active else MUTED,weight=True,live=True)
    text(pd,(40,406),'Stream1' if active else '--',23,WHITE,live=True)
    text(pd,(435,406),'48 kHz / 16-bit Stereo' if active else '--',23,WHITE,live=True)
    text(pd,(990,406),'Lost: 0',23,WHITE,live=True)
    text(pd,(398,481),'40 ms',24,GREEN,anchor='ra',live=True)
    text(pd,(798,481),'0.0 dB',24,GREEN,anchor='ra',live=True)
    for n,title in enumerate(('AUTO','VBAN Only','AirPlay Only')):
        preview.paste(Image.open(SKIN/(title.replace(' ','_')+('_on.png' if n==0 else '_off.png'))),(40+n*410,285))
    for x,frame in ((60,27),(460,84)):
        preview.paste(strip.crop((0,frame*h,w,(frame+1)*h)),(x,520))
    meter=Image.open(SKIN/'terminal-meter-on.png'); off=Image.open(SKIN/'terminal-meter-off.png')
    for y,width in ((509,218),(541,181)):
        preview.paste(off,(890,y))
        if active: preview.paste(meter.crop((0,0,width,20)),(890,y))
    preview.save(OUT/(state+'.png'))
    if state=='receiving':
        (ROOT/'build').mkdir(exist_ok=True); preview.save(ROOT/'build/UI-preview.png')
draft=OUT/'Plugin Skins'
if draft.exists(): shutil.rmtree(draft)
shutil.copytree(SKIN,draft)
print('MPC AirLink terminal skin generated:',SKIN)
