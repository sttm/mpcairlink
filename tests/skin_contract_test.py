"""Visibility/native-artwork contract; this does not emulate MPC rendering."""
from pathlib import Path
import json
from PIL import Image, ImageStat
ROOT=Path(__file__).resolve().parents[1];skin=ROOT/'skins'
tui=json.loads((skin/'TUI.json').read_text());page=tui['pageData'];tabs=page['tabs']
assert all(tab['qlinkBoundsData']==[] for tab in tabs) # no orange hardware-bank frame
main=tabs[0]['componentDefinition']['componentsData']
def name(e):return e['componentData']['name']
def param(e):
    return next((x['value'] for x in e['handle remapping']['map'] if x['key']=='Data'),None)
def conditional(e,mode):
    assert e['bounds']['showWhenDataModelInvalid']=='Hide',name(e)
    assert e['bounds']['additionalInvalidatingHandles']==[f'IndexedEnabling/{mode}/2/Parameter 14'],name(e)
address=[e for e in main if param(e)=='Parameter 4'];assert len(address)==1
conditional(address[0],1)
byname={name(e):e for e in main}
conditional(byname['AirPlay receiver'],0);conditional(byname['VBAN receiver'],1)
conditional(byname['VBAN active stream'],1);conditional(byname['VBAN lost'],1)
conditional(byname['AirPlay device hint'],0)
assert all(param(e)!='Parameter 13' for e in main) # no stale VBAN service/port text in AirPlay
for e in main:
    if e['componentData']['type']=='Label':
        style=e['componentData']['data']['textStyle'];assert style['font']['name']=='Roboto'
        assert set(style['justification'].split())<={'left','right','horizontallyCentred','verticallyCentred','top','bottom','horizontallyJustified'}
buttons=[e for e in main if e['componentData']['type']=='Button']
assert len(buttons)==2 and all(param(e)=='Parameter 14' for e in buttons)
assert [e['componentData']['data']['buttonId'] for e in buttons]==[0,1]
q=json.loads((skin/'Q-Links.json').read_text())['Program Mode Q-Links']
assert [q[f'Q-Link {n}'] for n in (1,2,3,4)]==[3,-1,-1,-1]
definitions={e['key']:e['value'] for e in page['componentDefinitions']['localComponentDefinitions']}
assert not any(param(e)=='Parameter 2' for e in main)
assert 'buffer' not in byname
diag=tabs[1]['componentDefinition']['componentsData']
assert any(name(e)=='VBAN buffer' and param(e)=='Parameter 2' for e in diag)
assert all(param(e)!='Parameter 15' for e in diag+main)
assert not any(skin.glob('refresh*.png'))
for mapping in json.loads((skin/'Q-Links.json').read_text())['Screen Mode Q-Links']['map']:
    assert list(mapping['Q-Links'].values())==[3]+[-1]*15
for name_,size,param_,phase in (('output',184,3,17),):
    parent=byname[name_];assert parent['bounds']['acceptsHWFocus']=='Yes'
    remap={v['key']:v['value'] for v in parent['handle remapping']['map']}
    assert remap=={'Data':f'Parameter {param_}','Phase':f'Parameter {phase}'}
    parts=definitions[name_+' control']['componentsData']
    assert not any(e['componentData']['type']=='Focus' for e in parts)
    assert [e['componentData']['name'] for e in parts]==['static body','center texture','rotor','fixed lighting','touch gesture']
    rotary=[e for e in parts if e['componentData']['type']=='Knob' and e['componentData']['data']['knobType']=='RotatingImage'];assert len(rotary)==1
    data=rotary[0]['componentData']['data']
    assert data['knobType']=='RotatingImage' and data['foregroundImage']==name_+'-rotor.png'
    assert data['backgroundImage']==name_+'-transparent.png' and data['handleName']=='Data'
    touch=parts[-1]['componentData']['data']
    assert touch['knobType']=='FilmStrip' and touch['numFrames']==2 and touch['filmStrip']==name_+'-touch.png'
    assert touch['handleName']==data['handleName']=='Data' and touch['dragOrientation']=='Vertical'
    assert parts[-1]['bounds']['bounds']==rotary[0]['bounds']['bounds'] # complete knob touch area
    center=parts[1]['componentData']['data'];assert center['handleName']=='Phase' and center['numFrames']==2
    for layer in ('base','rotor','light','transparent','center','touch'):
        with Image.open(skin/f'{name_}-{layer}.png') as im:
            assert im.mode=='RGBA' and im.size==(size,size*(2 if layer in ('center','touch') else 1))
            assert all(not(g>r+20 and g>b+20) for r,g,b,a in im.getdata() if a>240) # no green arc/debug mark
            if layer=='center':
                assert im.crop((0,0,size,size)).tobytes()!=im.crop((0,size,size,size*2)).tobytes()
            if layer in ('transparent','touch'):assert im.getchannel('A').getbbox() is None
    assert not (skin/f'{name_}-knob.png').exists() # no full motion filmstrip
with Image.open(skin/'meter-strip.png') as im:
    assert im.size==(330,28*23)
    for level in range(23):
        for segment in range(22):assert (im.getpixel((segment*15+5,level*28+12))!=(32,48,36))==(segment<level)
rgba=sum(Image.open(f).width*Image.open(f).height*4 for f in skin.glob('*.png'))
assert rgba<10*1024*1024
print(f'PASS layered skin: VBAN-only address/port, mode cards, native fonts/Q-Links; shared rotor, fixed light, two center frames, no Focus overlay; {rgba/1048576:.2f} MiB decoded artwork')
