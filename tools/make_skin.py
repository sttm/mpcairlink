#!/usr/bin/env python3
"""Generate the MPC AirLink native terminal skin, Q-Links and previews."""
from pathlib import Path
import sys, math
from PIL import Image, ImageDraw, ImageFont
from airlink_artwork import svg_icon, wordmark
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor/mpc-plugin-builder-sdk/tools'))
import gen_ui as ui
O=ui.obj
OUT=ROOT/'design/airlink-v1.1.1'; SKIN=ROOT/'skins'
import shutil
if SKIN.exists(): shutil.rmtree(SKIN)
SKIN.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
BG='#0a0d12'; PANEL='#181d25'; LINE='#303947'; GREEN='#8fe07a'; WHITE='#f0f3f7'; MUTED='#a2adbd'; DIM='#657387'
mono='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
bold='/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'
if not Path(mono).exists():
    mono='/System/Library/Fonts/Menlo.ttc'; bold=mono
sans='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
if not Path(sans).exists(): sans='/System/Library/Fonts/Supplemental/Arial.ttf'
def font(size,weight=False,live=False):
    f=ImageFont.truetype(sans if live else str(ROOT/'assets/fonts/SpaceGrotesk.ttf'),size)
    if not live: f.set_variation_by_axes([650 if weight else 450])
    return f
def text(draw,xy,label,size=18,color=MUTED,weight=False,anchor=None,live=False):
    draw.text(xy,label,font=font(size,weight,live),fill=color,anchor=anchor)
def rule(draw,xy,color=LINE): draw.line(xy,fill=color,width=1)
def box(draw,xy):
    # Gentle highlight baked once; the lower control area stays exactly PANEL.
    x0,y0,x1,y1=xy; radius=16
    base=tuple(bytes.fromhex(PANEL[1:]))
    for y in range(y0,y1+1):
        edge=min(y-y0,y1-y)
        inset=radius-math.sqrt(max(0,radius*radius-(radius-min(radius,edge))**2))
        lift=round(3*max(0,1-(y-y0)/max(1,(y1-y0)*.45)))
        draw.line((x0+inset,y,x1-inset,y),fill=tuple(c+lift for c in base))
    draw.rounded_rectangle(xy,radius=radius,outline=LINE,width=1)
panel=Image.new('RGB',(1280,628),BG); d=ImageDraw.Draw(panel)
# A terminal window, with clear hierarchy and touch-sized controls.
# Space Grotesk is baked into the PNG: no extra font load on the device.
panel.paste(wordmark(WHITE,BG),(40,13))
text(d,(40,61),'MPC / NETWORK RECEIVER',12,DIM)
rule(d,(40,78,1240,78))
box(d,(40,100,785,233)); box(d,(805,100,1240,233))
text(d,(60,114),'CONNECT TO THIS MPC',17)
text(d,(60,203),'UDP 6980   /   VBAN ACCEPTS ANY STREAM',16,DIM)
text(d,(825,114),'LINK STATUS',17)
text(d,(825,205),'LOCAL NETWORK RECEIVER',12,DIM)
# A tiny permanent ANY label replaces the entire filter control section.
text(d,(40,253),'INPUT SOURCE',17)
text(d,(1240,253),'AirPlay for Mac + iPhone',15,DIM,anchor='ra')
for x,title in [(40,'AirPlay'),(650,'VBAN')]:
    for on in (False,True):
        im=Image.new('RGB',(590,64),BG); b=ImageDraw.Draw(im)
        b.rounded_rectangle((0,0,589,63),radius=14,fill=GREEN if on else PANEL,outline=GREEN if on else LINE,width=1)
        ink=BG if on else WHITE
        if title=='AirPlay':
            im.paste(svg_icon(ROOT/'assets/icons/airplay.svg',44,ink,GREEN if on else PANEL),(16,8))
        else:
            for xx,hh in [(27,12),(37,30),(47,20)]:b.line((xx,32-hh/2,xx,32+hh/2),fill=ink,width=3)
        text(b,(76,32),title,25,ink,True,'lm')
        text(b,(564,32),'Mac / iPhone' if title=='AirPlay' else 'Windows / Android',17,ink if on else MUTED,anchor='rm')
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
text(d,(40,611),'LOCAL NETWORK AUDIO',12,DIM)
text(d,(1240,611),'sttm / MPC AIRLINK',12,DIM,anchor='ra')
panel.save(SKIN/'terminal-panel.png')
airplay_card=Image.new('RGB',(746,134),BG);ac=ImageDraw.Draw(airplay_card)
box(ac,(0,0,745,133))
text(ac,(20,14),'AIRPLAY RECEIVER',17)
text(ac,(20,43),'MPC AirLink',39,WHITE,True)
text(ac,(20,103),'SELECT MPC AIRLINK IN AIRPLAY',16,DIM)
airplay_card.save(SKIN/'airplay-card.png')

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
# Complete-frame segments: there is no reveal rectangle cutting through a block.
meter_strip=Image.new('RGB',(330,20*23),PANEL);md=ImageDraw.Draw(meter_strip)
for level in range(23):
    for i in range(22):
        colour=(GREEN if i<18 else '#d2cf76' if i<21 else '#e88578') if i<level else '#263a2b'
        md.rectangle((i*15,level*20+2,i*15+10,level*20+17),fill=colour)
meter_strip.save(SKIN/'terminal-meter-strip.png')
for value in (10,24):
    for state in ('off','on'):
        im=Image.new('RGB',(180,48),BG);rd=ImageDraw.Draw(im)
        rd.rounded_rectangle((0,0,179,47),radius=10,fill=GREEN if state=='on' else PANEL,outline=LINE)
        text(rd,(90,24),str(value)+' Hz',23,BG if state=='on' else WHITE,True,'mm')
        im.save(SKIN/f'refresh{value}_{state}.png')
E=ui.entry

def entry(name,typ,data,bounds,param=None,focus='No',conds=None):
    return E(name,typ,data,bounds,focus,'Show','Always',remap=[] if param is None else [('Data',f'Parameter {param}')],invalidating=conds)
children=[entry('terminal panel','Image',O(('version',2),('imageType','Regular'),('colour','00000000'),('image','terminal-panel.png')),'0 0 1280 628')]

def label(name,p,bounds,height=32,color='ffe3eadf',right=False,conds=None):
    data=ui.label_data('Value',color,height,'right verticallyCentred' if right else 'left verticallyCentred')
    # Roboto is provided by MPC; all fixed text is baked in an OFL/Bitstream mono font.
    for key,value in data:
        if key=='textStyle':
            for k,v in value:
                if k=='font':
                    for i,(fk,fv) in enumerate(v):
                        if fk=='name': v[i]=(fk,'Roboto')
    children.append(entry(name,'Label',data,bounds,p,conds=conds))
children.append(entry('AirPlay receiver card','Image',O(('version',2),('imageType','Regular'),('colour','00000000'),('image','airplay-card.png')),'40 100 746 134',conds=['IndexedEnabling/0/2/Parameter 14']))
label('address',4,'60 145 705 51',42,conds=['IndexedEnabling/1/2/Parameter 14'])
label('connection',5,'825 151 390 49',38,'ff8fe07a')
label('stream',6,'40 403 350 32',30)
label('format',7,'435 403 510 32',30)
label('lost',8,'990 403 250 32',30)
for n,title in enumerate(('AirPlay','VBAN')):
    fn=title.replace(' ','_')
    children.append(entry(title,'Button',ui.button_data(fn+'_on.png',fn+'_off.png',n,2),f'{40+n*610} 285 590 64',14))
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
    children.append(entry('level '+str(p),'Image',O(('version',2),('imageType','FilmStrip'),('colour','00000000'),('image','terminal-meter-strip.png'),('numFrames',23),('handleName','Data'),('animated',False)),f'890 {y} 330 20',p))
# Diagnostics stays off the main performance page.
main_children=children
page=Image.new('RGB',(1280,628),BG); dd=ImageDraw.Draw(page)
text(dd,(40,25),'>_ AIRLINK DIAGNOSTICS',30,WHITE,True)
text(dd,(1240,40),'sttm / MPC AIRLINK',16,MUTED,anchor='rm');rule(dd,(40,78,1240,78))
for bounds,title in [((40,104,420,230),'PACKETS LOST'),((440,104,820,230),'AUDIO DROPPED'),((840,104,1240,230),'UNDERRUNS'),((40,252,1240,366),'SERVICE / BUFFER'),((40,388,620,500),'ACTIVE STREAM'),((640,388,1240,500),'AUDIO FORMAT')]:
    box(dd,bounds);text(dd,(bounds[0]+20,bounds[1]+16),title,17)
text(dd,(40,538),'METER REFRESH',17,MUTED)
text(dd,(40,567),'10 Hz: lower UI traffic   /   24 Hz: smoother levels',16,DIM)
page.save(SKIN/'terminal-diagnostics.png')
children=[entry('diagnostics panel','Image',O(('version',2),('imageType','Regular'),('colour','00000000'),('image','terminal-diagnostics.png')),'0 0 1280 628')]
for name,param,bounds in [('lost packets',8,'60 151 340 55'),('dropped frames',11,'460 151 340 55'),('underruns',12,'860 151 360 55'),('service',13,'60 298 1160 47'),('active stream',6,'60 432 540 48'),('audio format',7,'660 432 560 48')]:
    label(name,param,bounds,36,'ff8fe07a')
for n,value in enumerate((10,24)):
    children.append(entry('meter refresh '+str(value),'Button',ui.button_data(f'refresh{value}_on.png',f'refresh{value}_off.png',n,2),f'{840+n*200} 530 180 48',15))
diag_children=children
children=main_children

defs=[('terminal fader',slider),('terminal editor',ui.overlay_component('KnobOverlay',ui.knob_overlay_data(False),'ff0b100d'))]
tabs=[]
for index,name,items,bounds in [(0,'STREAM',main_children,['40 245 1200 336']),(1,'DIAG',diag_children,[])]:
    tabs.append(O(('version',1),('tabName',name),('fnKeyIndex',index),('fnKeySubIndex',0),('componentDefinition',ui.component_definition([],items,'ff0b100d')),('qlinkBoundsData',bounds)))
tui=O(('pageData',O(('version',1),('componentDefinitions',O(('version',2),('importFiles',[]),('localComponentDefinitions',[O(('key',k),('value',v)) for k,v in defs]))),('replacementStrings',[]),('info',O(('version',1),('type','CompleteDescription'))),('tabs',tabs))))
qmap=O(*[(f'Q-Link {q}',{1:14,2:2,3:3}.get(q,-1)) for q in range(1,17)])
none=O(*[(f'Q-Link {q}',15 if q==1 else -1) for q in range(1,17)])
maps=[O(('Tab',1),('SubTab',1),('Bank Direction','Row'),('Q-Links',qmap)),O(('Tab',2),('SubTab',1),('Bank Direction','Row'),('Q-Links',none))]
ql=O(('version',4),('info',O(('version',1),('type','CompleteDescription'))),('Screen Mode Q-Links',O(('version',4),('map',maps))),('Program Mode Q-Links',qmap))
(SKIN/'TUI.json').write_text(ui.dump_json(tui)+'\n');(SKIN/'Q-Links.json').write_text(ui.dump_json(ql)+'\n')
for state in ('receiving','waiting','vban'):
    preview=panel.copy(); pd=ImageDraw.Draw(preview)
    active=state!='waiting'
    if state=='vban':text(pd,(60,149),'192.0.2.10 : 6980',34,WHITE,live=True)
    else:preview.paste(airplay_card,(40,100))
    text(pd,(825,154),'RECEIVING' if active else 'WAITING _',32,GREEN if active else MUTED,weight=True,live=True)
    text(pd,(40,406),('Stream1' if state=='vban' else 'AirPlay') if active else '--',23,WHITE,live=True)
    text(pd,(435,406),('48 kHz / 16-bit Stereo' if state=='vban' else '44.1 kHz / 16-bit Stereo') if active else '--',23,WHITE,live=True)
    text(pd,(990,406),'Lost: 0',23,WHITE,live=True)
    text(pd,(398,481),'40 ms',24,GREEN,anchor='ra',live=True)
    text(pd,(798,481),'0.0 dB',24,GREEN,anchor='ra',live=True)
    for n,title in enumerate(('AirPlay','VBAN')):
        preview.paste(Image.open(SKIN/(title.replace(' ','_')+('_on.png' if n==(1 if state=='vban' else 0) else '_off.png'))),(40+n*610,285))
    for x,frame in ((60,27),(460,84)):
        preview.paste(strip.crop((0,frame*h,w,(frame+1)*h)),(x,520))
    for y,level in ((509,14),(541,12)):
        frame=level if active else 0
        preview.paste(meter_strip.crop((0,frame*20,330,(frame+1)*20)),(890,y))
    preview.save(OUT/(state+'.png'))
    if state=='receiving':
        (ROOT/'build').mkdir(exist_ok=True); preview.save(ROOT/'build/UI-preview.png')
draft=OUT/'Plugin Skins'
if draft.exists(): shutil.rmtree(draft)
shutil.copytree(SKIN,draft)
print('MPC AirLink terminal skin generated:',SKIN)
