#!/usr/bin/env python3
"""Offline physical AirLink skin. Native labels/knobs; no runtime lighting."""
from pathlib import Path
import sys, math, shutil, json
from PIL import Image, ImageDraw, ImageFont, ImageChops
from airlink_artwork import svg_icon, wordmark
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor/mpc-plugin-builder-sdk/tools'))
import gen_ui as ui
O=ui.obj; SKIN=ROOT/'skins'; OUT=ROOT/'design/airlink-v1.3.0'
if SKIN.exists():shutil.rmtree(SKIN)
SKIN.mkdir();OUT.mkdir(parents=True,exist_ok=True)
GREEN='#8fe07a';WHITE='#f0f3ed';MUTED='#a8afa9';DIM='#738078';DARK='#0c100e'
sans='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
if not Path(sans).exists():sans='/System/Library/Fonts/Supplemental/Arial.ttf'
def font(size,bold=False,live=False):
    f=ImageFont.truetype(sans if live else str(ROOT/'assets/fonts/SpaceGrotesk.ttf'),size)
    if not live:f.set_variation_by_axes([650 if bold else 450])
    return f
def text(d,xy,label,size=18,color=MUTED,bold=False,anchor=None,live=False):
    d.text(xy,label,font=font(size,bold,live),fill=color,anchor=anchor)
def logo(im):
    mark=wordmark(WHITE,'#000000').resize((322,53),Image.Resampling.LANCZOS)
    im.paste(Image.new('RGB',mark.size,WHITE),(76,35),mark.convert('L'))
    text(ImageDraw.Draw(im),(76,96),'NETWORK AUDIO RECEIVER',16,WHITE)
base=Image.open(ROOT/'assets/airlink-physical-v3/panel-unlabelled.png').convert('RGB').resize((1280,628),Image.Resampling.LANCZOS)
panel=base.copy();logo(panel);d=ImageDraw.Draw(panel)
for x in (340,881):d.line((x,166,x,254),fill='#566058',width=1)
text(d,(68,165),'STATUS',15)
text(d,(904,165),'AUDIO FORMAT',15)
text(d,(68,311),'SOURCE',19,WHITE)
text(d,(610,308),'OUTPUT',22,WHITE,anchor='mm')
text(d,(860,343),'STEREO LEVEL',20,WHITE)
text(d,(863,413),'L',23,WHITE,anchor='mm');text(d,(863,467),'R',23,WHITE,anchor='mm')
for cx,cy,r in ((610,430,109),):
    for step in range(9):
        a=math.radians(135+step*270/8)
        d.line((cx+math.cos(a)*r,cy+math.sin(a)*r,cx+math.cos(a)*(r+6),cy+math.sin(a)*(r+6)),fill=MUTED,width=2)
panel.save(SKIN/'physical-panel.png')
# Mode-specific panels share a sampled glass background; no stale IP or port
# is baked into AirPlay artwork. Every conditional widget hides when invalid.
mode_bounds=(350,150,875,268)
for mode in ('airplay','vban'):
    im=panel.crop(mode_bounds);md=ImageDraw.Draw(im)
    text(md,(15,15),'AIRPLAY RECEIVER' if mode=='airplay' else 'MPC IP / UDP',15)
    if mode=='airplay':
        text(md,(15,45),'MPC AirLink',36,WHITE,True)
        text(md,(15,96),'SELECT MPC AIRLINK IN AIRPLAY',15,MUTED)
    else:text(md,(15,96),'STREAM',14,MUTED)
    im.save(SKIN/f'{mode}-display.png')
hint=panel.crop((895,234,1210,268));text(ImageDraw.Draw(hint),(9,7),'MAC / IPHONE',16,MUTED)
hint.save(SKIN/'airplay-hint.png')
# Existing CC0 SVG remains the actual AirPlay icon; the generated art has no icon.
buttons={}
for n,title in enumerate(('AirPlay','VBAN')):
    y=(343,462)[n];bounds=(45,y,330,y+96)
    for on in (False,True):
        im=panel.crop(bounds);bd=ImageDraw.Draw(im)
        if on:
            bd.rounded_rectangle((4,4,280,91),radius=18,outline=GREEN,width=3)
            bd.rounded_rectangle((8,8,276,87),radius=15,outline='#517846',width=1)
        ink=GREEN if on else WHITE
        if n==0:
            mark=svg_icon(ROOT/'assets/icons/airplay.svg',48,'#ffffff','#000000').convert('L')
            im.paste(Image.new('RGB',(48,48),ink),(24,24),mark)
        else:
            for xx,hh in ((33,25),(45,43),(57,31)):bd.line((xx,48-hh/2,xx,48+hh/2),fill=ink,width=3)
        text(bd,(163,48),title.upper(),26,ink,True,'mm')
        fn=title+('_on.png' if on else '_off.png');im.save(SKIN/fn);buttons[(n,on)]=im
# Experimental layered native knobs: one rotor contains both teeth and index.
# Fixed RGBA lighting is a separate ordinary PNG; center has only two frames.
render_dir=ROOT/'assets/airlink-layered-knob-v2';frames=2;knobs={}
for name,cx,cy,size in (('output',610,430,184),):
    x,y=cx-size//2,cy-size//2;layers={}
    for layer,source in (('base','01-static'),('rotor','05-rotor'),('light','04-fixed-light')):
        im=Image.open(render_dir/(source+'.png')).convert('RGBA').resize((size,size),Image.Resampling.LANCZOS)
        im.save(SKIN/f'{name}-{layer}.png');layers[layer]=im
    strip=Image.new('RGBA',(size,size*2))
    for frame,source in enumerate(('03-center-a','03-center-b')):
        im=Image.open(render_dir/(source+'.png')).convert('RGBA').resize((size,size),Image.Resampling.LANCZOS)
        strip.paste(im,(0,frame*size))
    strip.save(SKIN/f'{name}-center.png');layers['center']=strip
    Image.new('RGBA',(size,size)).save(SKIN/f'{name}-transparent.png')
    # A proven FilmStrip control above every decorative layer owns the gesture.
    # Its two frames are invisible; it edits the same Data as the native rotor.
    Image.new('RGBA',(size,size*2)).save(SKIN/f'{name}-touch.png')
    knobs[name]=(layers,x,y,size)
def knob_frame(name,value):
    layers,x,y,size=knobs[name];phase=int(max(0,min(1,value))*54)%2
    im=layers['base'].copy();im.alpha_composite(layers['center'].crop((0,phase*size,size,(phase+1)*size)))
    im.alpha_composite(layers['rotor'].rotate(135-270*value,resample=Image.Resampling.BICUBIC))
    im.alpha_composite(layers['light']);return im
def knob_preview(target,name,value):
    layers,x,y,size=knobs[name];im=knob_frame(name,value);target.paste(im,(x,y),im)
# Atomic complete frames: LED rows never expose half a segment.
meter=Image.new('RGB',(330,28*23));md=ImageDraw.Draw(meter)
for level in range(23):
    md.rectangle((0,level*28,329,(level+1)*28-1),fill='#080c09')
    for i in range(22):
        color=(GREEN if i<18 else '#d2cf76' if i<21 else '#e88578') if i<level else '#203024'
        md.rounded_rectangle((i*15+1,level*28+3,i*15+11,level*28+24),radius=1,fill=color)
meter.save(SKIN/'meter-strip.png')
# Diagnostics: one static glass panel, native values; same meter scheduler as 1.1.1.
diag=base.copy();logo(diag);dd=ImageDraw.Draw(diag)
text(dd,(1190,70),'DIAGNOSTICS',25,WHITE,True,'rm')
dd.rounded_rectangle((40,134,1240,586),radius=18,fill='#0c100e',outline='#667169',width=2)
for x,title in ((65,'PACKETS LOST'),(455,'AUDIO DROPPED'),(850,'UNDERRUNS')):text(dd,(x,156),title,17)
for x in (430,823):dd.line((x,155,x,251),fill='#303b33')
text(dd,(65,280),'SERVICE / BUFFER',16)
text(dd,(65,380),'ACTIVE STREAM',16);text(dd,(665,380),'AUDIO FORMAT',16)
text(dd,(65,486),'VBAN BUFFER',17)
dd.rounded_rectangle((65,512,285,560),radius=8,fill='#101813',outline='#667169',width=1)
text(dd,(305,536),'AIRPLAY: FIXED 120 ms',16,DIM,anchor='lm')
diag.save(SKIN/'physical-diagnostics.png')
def entry(name,typ,data,bounds,param=None,focus='No',conds=None):
    return ui.entry(name,typ,data,bounds,focus,'Hide' if conds else 'Show','Always',remap=[] if param is None else [('Data',f'Parameter {param}')],invalidating=conds)
def image(name,file,bounds,param=None,conds=None,frame_count=None):
    data=O(('version',2),('imageType','FilmStrip' if frame_count else 'Regular'),('colour','00000000'),('image',file))
    if frame_count:data+=O(('numFrames',frame_count),('handleName','Data'),('animated',False))
    return entry(name,'Image',data,bounds,param,conds=conds)
def label(name,param,bounds,height=28,color='fff0f3ed',conds=None,center=False):
    data=ui.label_data('Value',color,height,'horizontallyCentred verticallyCentred' if center else 'left verticallyCentred')
    for key,value in data:
        if key=='textStyle':
            for k,v in value:
                if k=='font':
                    for j,(fk,fv) in enumerate(v):
                        if fk=='name':v[j]=(fk,'Roboto')
    return entry(name,'Label',data,bounds,param,conds=conds)
conditions={n:[f'IndexedEnabling/{n}/2/Parameter 14'] for n in (0,1)}
children=[image('physical panel','physical-panel.png','0 0 1280 628')]
children += [image('AirPlay receiver','airplay-display.png','350 150 525 118',conds=conditions[0]),image('VBAN receiver','vban-display.png','350 150 525 118',conds=conditions[1])]
children.append(label('connection',5,'68 198 255 45',29,'ff8fe07a'))
children.append(label('VBAN IP and port',4,'365 195 495 46',32,'ff8fe07a',conditions[1]))
children.append(label('VBAN active stream',6,'445 240 410 29',19,conds=conditions[1]))
children.append(label('format',7,'904 195 300 37',23))
children.append(label('VBAN lost',8,'904 237 300 29',21,conds=conditions[1]))
children.append(image('AirPlay device hint','airplay-hint.png','895 234 315 34',conds=conditions[0]))
for n,title in enumerate(('AirPlay','VBAN')):
    children.append(entry(title,'Button',ui.button_data(title+'_on.png',title+'_off.png',n,2),f'45 {(343,462)[n]} 285 96',14))
defs=[]
for name,param,phase in (('output',3,17),):
    layers,x,y,size=knobs[name];bounds=f'0 0 {size} {size}'
    center=image('center texture',name+'-center.png',bounds,frame_count=2)
    # Phase is explicitly remapped at the parent alongside the primary Data.
    for key,value in center:
        if key=='componentData':
            for ck,cv in value:
                if ck=='data':
                    for j,(dk,dv) in enumerate(cv):
                        if dk=='handleName':cv[j]=(dk,'Phase')
    rotor=O(('version',4),('knobType','RotatingImage'),('foregroundImage',name+'-rotor.png'),('backgroundImage',name+'-transparent.png'),('imageScale',1.0),('dragOrientation','Vertical'),('handleName','Data'))
    touch=entry('touch gesture','Knob',ui.knob_filmstrip_data(name+'-touch.png',2,'Vertical'),bounds)
    parts=[image('static body',name+'-base.png',bounds),center,entry('rotor','Knob',rotor,bounds),image('fixed lighting',name+'-light.png',bounds),touch]
    defs.append((name+' control',ui.component_definition(ui.control_actions('hardware editor'),parts,'00000000')))
    control=entry(name,name+' control',O(('version',1),('handleName','Data')),f'{x} {y} {size} {size}',param,'Yes')
    for key,value in control:
        if key=='handle remapping':
            for mk,mv in value:
                if mk=='map':mv.append(O(('key','Phase'),('value',f'Parameter {phase}')))
    children.append(control)
children.append(label('output value',3,'530 530 160 34',29,'ff8fe07a',center=True))
for p,y in ((9,398),(10,453)):children.append(image('level '+str(p),'meter-strip.png',f'899 {y} 330 28',p,frame_count=23))
main_children=children
children=[image('diagnostics panel','physical-diagnostics.png','0 0 1280 628')]
for name,param,bounds,height in [('lost packets',8,'65 190 335 48',34),('dropped frames',11,'455 190 335 48',34),('underruns',12,'850 190 345 48',34),('service',13,'65 313 1130 47',31),('stream',6,'65 412 540 45',31),('format',7,'665 412 530 45',31)]:children.append(label(name,param,bounds,height,'ff8fe07a'))
# Proven transparent FilmStrip receives the gesture; a native label shows ms.
Image.new('RGBA',(220,48*2)).save(SKIN/'buffer-setting-touch.png')
buffer_parts=[label('buffer ms',None,'0 0 220 48',27,'ff8fe07a',center=True),entry('buffer touch','Knob',ui.knob_filmstrip_data('buffer-setting-touch.png',2,'Vertical'),'0 0 220 48')]
buffer_actions=[action for action in ui.control_actions('hardware editor') if ('onAction','Mouse Down') not in action]
defs.append(('buffer setting',ui.component_definition(buffer_actions,buffer_parts,'00000000')))
children.append(entry('VBAN buffer','buffer setting',O(('version',1),('handleName','Data')),'65 512 220 48',2,'Yes'))
diag_children=children
defs.append(('hardware editor',ui.overlay_component('KnobOverlay',ui.knob_overlay_data(False),'ff0b100d')))
tabs=[]
for i,name,items,bounds in ((0,'STREAM',main_children,[]),(1,'DIAG',diag_children,[])):
    tabs.append(O(('version',1),('tabName',name),('fnKeyIndex',i),('fnKeySubIndex',0),('componentDefinition',ui.component_definition([],items,'ff0b100d')),('qlinkBoundsData',bounds)))
tui=O(('pageData',O(('version',1),('componentDefinitions',O(('version',2),('importFiles',[]),('localComponentDefinitions',[O(('key',k),('value',v)) for k,v in defs]))),('replacementStrings',[]),('info',O(('version',1),('type','CompleteDescription'))),('tabs',tabs))))
qmap=O(*[(f'Q-Link {q}',3 if q==1 else -1) for q in range(1,17)])
none=qmap
maps=[O(('Tab',1),('SubTab',1),('Bank Direction','Row'),('Q-Links',qmap)),O(('Tab',2),('SubTab',1),('Bank Direction','Row'),('Q-Links',none))]
ql=O(('version',4),('info',O(('version',1),('type','CompleteDescription'))),('Screen Mode Q-Links',O(('version',4),('map',maps))),('Program Mode Q-Links',qmap))
(SKIN/'TUI.json').write_text(ui.dump_json(tui)+'\n');(SKIN/'Q-Links.json').write_text(ui.dump_json(ql)+'\n')
# Standalone previews substitute only the same native-dynamic regions.
for state in ('receiving','waiting','vban'):
    im=panel.copy();pd=ImageDraw.Draw(im);vban=state=='vban';active=state!='waiting'
    im.paste(Image.open(SKIN/('vban-display.png' if vban else 'airplay-display.png')),(350,150))
    text(pd,(68,206),'RECEIVING' if active else 'WAITING',27,GREEN if active else MUTED,True,live=True)
    if vban:
        text(pd,(365,203),'192.0.2.42 : 6980',30,GREEN,live=True)
        text(pd,(445,247),'Stream1',17,WHITE,live=True)
    text(pd,(904,202),('48 kHz / 16-bit Stereo' if vban else '44.1 kHz / 16-bit Stereo') if active else '--',21,WHITE,live=True)
    if vban:text(pd,(904,243),'Lost: 0',16,MUTED,live=True)
    else:im.paste(Image.open(SKIN/'airplay-hint.png'),(895,234))
    for n in (0,1):im.paste(buttons[(n,n==int(vban))],(45,(343,462)[n]))
    knob_preview(im,'output',24/36)
    text(pd,(610,547),'0.0 dB',27,GREEN,anchor='mm',live=True)
    for y,level in ((398,14),(453,12)):
        frame=level if active else 0;im.paste(meter.crop((0,frame*28,330,(frame+1)*28)),(899,y))
    im.save(OUT/f'{state}.png')
    if state=='receiving':(ROOT/'build').mkdir(exist_ok=True);im.save(ROOT/'build/UI-preview.png')
diagnostic_preview=diag.copy();dd=ImageDraw.Draw(diagnostic_preview)
text(dd,(175,536),'120 ms',27,GREEN,anchor='mm',live=True)
diagnostic_preview.save(OUT/'diagnostics.png')
# Offline preview only: rotation/interpolation on MPC is performed by its UI.
sheet=Image.new('RGB',(6*200,210),'#151a17')
for cell in range(6):
    im=knob_frame('output',cell/5);sheet.paste(im,(cell*200+8,8),im)
sheet.save(OUT/'knob-positions.png')
rgba=sum(Image.open(f).width*Image.open(f).height*4 for f in SKIN.glob('*.png'))
(OUT/'artwork-budget.json').write_text(json.dumps({'png_count':len(list(SKIN.glob('*.png'))),'decoded_rgba_bytes':rgba,'knob_frames':2,'knob_rendering':'native RotatingImage: shared teeth/index; fixed light; two center frames','runtime_material_rendering':False},indent=2)+'\n')
print('Physical AirLink skin generated:',SKIN,'decoded RGBA MiB:',round(rgba/1048576,2))
