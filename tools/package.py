#!/usr/bin/env python3
import hashlib, json, shutil, subprocess, sys, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor/mpc-plugin-builder-sdk/tools'))
from build import write_version_xml
out=ROOT/'build/VST2 Plugins/sttm - VST - MPC AirLink'
subprocess.run([sys.executable,str(ROOT/"tools/verify_airplay.py")],check=True)
shutil.copytree(ROOT/'Content',out/'Content',dirs_exist_ok=True,ignore=shutil.ignore_patterns('*native*'))
shutil.copy2(ROOT/'plugin.json',out/'plugin.json')
if (out/'Plugin Skins').exists(): shutil.rmtree(out/'Plugin Skins')
shutil.copytree(ROOT/'skins',out/'Plugin Skins')
manifest=json.loads((ROOT/'plugin.json').read_text())
write_version_xml(str(out),manifest,True)
for f in ('README.md','LICENSE','THIRD_PARTY.md'): shutil.copy2(ROOT/f,out/f)
validation=ROOT/'build'/('AIRLINK-'+manifest['version']+'-VALIDATION.md')
if not validation.exists(): validation=ROOT/'docs/VALIDATION.md'
if validation.exists(): shutil.copy2(validation,out/'VALIDATION.md')
if (ROOT/'README.ru.md').exists(): shutil.copy2(ROOT/'README.ru.md',out/'README.ru.md')
subprocess.run([sys.executable,str(ROOT/'vendor/mpc-plugin-builder-sdk/tools/validate.py'),str(out),'--params',str(ROOT/'build/params.json')],check=True)
shutil.copy2(ROOT/'assets/fonts/SpaceGrotesk-OFL.txt',out/'ARTWORK-FONT-LICENSE.txt')
# Ship upstream SDK licence and the font licence with the artwork.
shutil.copy2(ROOT/'vendor/mpc-plugin-builder-sdk/LICENSE',out/'SDK-LICENSE.txt')
font_license=Path('/usr/share/doc/fonts-dejavu-core/copyright')
if font_license.exists(): shutil.copy2(font_license,out/'FONT-LICENSE.txt')
archive=ROOT/('dist/mpcairlink-'+manifest['version']+'-mpc.zip'); archive.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(out.rglob('*')):
        if f.is_file(): z.write(f,f.relative_to(ROOT/'build'))
    z.write(ROOT/'README.md','INSTALL.md')
sha=hashlib.sha256(archive.read_bytes()).hexdigest()
archive.with_suffix('.zip.sha256').write_text(sha+'  '+archive.name+'\n')
print('Package:',archive,'\nSHA256:',sha)
