"""Validate native icon slots, pixel payloads and BC3 atlas crops."""
from pathlib import Path
import csv,json
from collections import defaultdict
from PIL import Image,ImageChops,ImageStat
root=Path('work/faction-package/widgetui')
native=Path(r'E:\SteamLibrary\steamapps\common\AoE2DE\widgetui')
for file in ('icons.json','materials.json'):assert (root/file).read_bytes()==(native/file).read_bytes()
icons=json.loads((root/'icons.json').read_text());materials=json.loads((root/'materials.json').read_text())
defs={r['MaterialDef']['Name']:r['MaterialDef'] for r in materials['Materials']}
atlases={r['AtlasDef']['Name']:r['AtlasDef'] for r in materials['AtlasTextures']}
target={(r['kind'],int(r['civ']) if r['kind']=='unit' else -1,int(r['id'])):int(r['icon']) for r in csv.DictReader(open('work/faction-target-dependencies/language-ids.tsv'),delimiter='\t')}
units={(int(r['civ']),int(r['id'])):r for r in csv.DictReader(open('work/faction-target/units.tsv'),delimiter='\t')}
for (kind,civ,uid),icon in target.items():
    unit=units.get((civ,uid))
    category='Techs' if kind=='tech' else 'Buildings' if unit['type']=='80' and unit['class'] not in ('34','36') else 'Units'
    assert icon==-1 or f'{icon:03d}' in icons[category],('Out-of-range icon',kind,civ,uid,category,icon)
assert target['unit',0,414]==target['unit',0,7067]==-1, 'Savannah tree icons must not index past the native vector'
report=json.loads(Path('outputs/faction-icon-ui-report.json').read_text());regions=defaultdict(list)
for r in report['bindings']:
    key=(r['kind'],r['civ'],r['id']);assert target[key]==r['icon'],key
    material=icons[r['category']][f"{r['icon']:03d}"];assert material==r['material']
    definition=defs[material];atlas=atlases[definition['AtlasRef']]
    texture=next(x for x in atlas['Textures'] if x['RefName']==definition['TextureRef'])
    image=Image.open(root/texture['FileName']).convert('RGBA')
    expected=Image.open(r['source_png']).convert('RGBA').resize(image.size,Image.Resampling.NEAREST)
    assert image.tobytes()==expected.tobytes(),key
for r in report['atlas_regions']:regions[r['atlas']].append(r)
errors=[]
for file,rows in regions.items():
    assert (root/file).read_bytes()[84:88]==b'DXT5'
    atlas=Image.open(root/file).convert('RGBA')
    for r in rows:
        crop=atlas.crop(tuple(r['box']))
        expected=Image.open(r['source_png']).convert('RGBA').resize(crop.size,Image.Resampling.NEAREST)
        error=max(ImageStat.Stat(ImageChops.difference(crop,expected)).mean)
        errors.append(error)
        if error>=8:print('BC3 crop error',round(error,3),file,r['box'],r['source_png'],flush=True)
assert target['unit',2,550]==target['unit',2,556]
result=dict(bindings=len(report['bindings']),all_icon_records_checked=len(target),native_slots=report['native_slots'],native_json_unchanged=True,atlas_files=len(regions),checked_regions=len(errors),maximum_mean_channel_error=max(errors),engine_ui_verified=False)
Path('outputs/faction-icon-validation.json').write_text(json.dumps(result,indent=2));print(result)
assert max(errors)<8,'Atlas compression or placement requires review'
