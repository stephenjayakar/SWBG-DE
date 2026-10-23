"""Use existing DE icon slots and atlases; no custom material registration."""
from pathlib import Path
import csv,json,hashlib,struct,subprocess
from collections import defaultdict
from PIL import Image
native=Path(r'E:\SteamLibrary\steamapps\common\AoE2DE\widgetui')
dest=Path('work/faction-package/widgetui');dest.mkdir(parents=True,exist_ok=True)
scratch=Path('work/native-icon-atlases');scratch.mkdir(parents=True,exist_ok=True)
icons=json.loads((native/'icons.json').read_text())
from faction_icon_limits import write_limits
write_limits(icons)
materials=json.loads((native/'materials.json').read_text())
defs={r['MaterialDef']['Name']:r['MaterialDef'] for r in materials['Materials']}
atlases={r['AtlasDef']['Name']:r['AtlasDef'] for r in materials['AtlasTextures']}
available=defaultdict(list)
for category in ('Units','Buildings','Techs'):
    for k,v in icons[category].items():
        if v not in defs or defs[v]['Type']!='Atlas':continue
        definition=defs[v];atlas=atlases[definition['AtlasRef']]
        texture=next(x for x in atlas['Textures'] if x['RefName']==definition['TextureRef'])
        # A handful of native technology slots are only 80px command images.
        # Reserve full-size portrait slots so SD compression retains source detail.
        if min(Image.open(native/texture['FileName']).size)<255:continue
        available[category].append(int(k))
units={(r['civ'],r['id']):r for r in csv.DictReader(open('work/faction-source/units.tsv'),delimiter='\t')}
chosen={};differences=[]
for row in json.loads(Path('outputs/faction-icon-report.json').read_text())['bindings']:
    c={1:1,3:2}[int(row['civ'])];u=int(row['id']);kind=row['kind']
    key=(kind,c if kind=='unit' else -1,u)
    png=Path(f'work/faction-icon-png/{row["civ"]}_{kind}_{u}.png')
    if key in chosen:
        if png.read_bytes()!=chosen[key]['png'].read_bytes():differences.append(u)
        continue
    category='Techs' if kind=='tech' else 'Buildings' if units[(row['civ'],row['id'])]['type']=='80' and units[(row['civ'],row['id'])]['class'] not in ('34','36') else 'Units'
    chosen[key]=dict(kind=kind,civ=key[1],id=u,png=png,category=category)
slots=defaultdict(dict);paint=defaultdict(list);bindings=[]
for record in chosen.values():
    original=Image.open(record['png']).convert('RGBA')
    digest=hashlib.sha256(original.tobytes()).hexdigest();category=record['category']
    if digest not in slots[category]:
        ordinal=len(slots[category]);assert ordinal<len(available[category]),('Native icon capacity exceeded',category,ordinal)
        index=available[category][ordinal]
        slots[category][digest]=index
        material=icons[category][f'{index:03d}'];definition=defs[material]
        assert definition['Type']=='Atlas'
        atlas=atlases[definition['AtlasRef']]
        texture=next(x for x in atlas['Textures'] if x['RefName']==definition['TextureRef'])
        paint[atlas['Name']].append((texture,original,record['png']))
        template=(native/texture['FileName']).read_bytes()
        w,h=Image.open(native/texture['FileName']).size
        image=original.resize((w,h),Image.Resampling.NEAREST)
        header=bytearray(template[:128]);assert header[:4]==b'DDS '
        struct.pack_into('<I',header,8,0x2100f);struct.pack_into('<I',header,20,w*4)
        struct.pack_into('<I',header,28,1)
        struct.pack_into('<8I',header,76,32,0x41,0,32,0xff,0xff00,0xff0000,0xff000000)
        path=dest/texture['FileName'];path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(header+image.tobytes())
        assert Image.open(path).convert('RGBA').tobytes()==image.tobytes()
    index=slots[category][digest]
    bindings.append({k:record[k] for k in ('kind','civ','id','category')}|dict(icon=index,material=icons[category][f'{index:03d}'],source_png=record['png'].as_posix()))
expected_files={texture['FileName'] for entries in paint.values() for texture,original,png in entries}
for old in (dest/'textures/ingame').rglob('*.dds'):
    assert old.resolve().is_relative_to((dest/'textures/ingame').resolve())
    if old.relative_to(dest).as_posix() not in expected_files:old.unlink()
tool=native.parent/'Tools_Builds/texconv.exe';regions=[]
for name,entries in paint.items():
    atlas=atlases[name]
    for source in sorted({atlas[k] for k in ('SDSource','HDSource','UHDSource','DefaultSource') if k in atlas}):
        image=Image.open(native/source).convert('RGBA');w,h=image.size
        for texture,original,png in entries:
            box=tuple(round(float(texture[k])*dimension+adjust) for k,dimension,adjust in (
                ('imageTLX',w,-.5),('imageTLY',h,-.5),('imageBRX',w,.5),('imageBRY',h,.5)))
            x,y,right,bottom=box;assert 0<=x<right<=w and 0<=y<bottom<=h
            image.paste(original.resize((right-x,bottom-y),Image.Resampling.NEAREST),(x,y))
            regions.append(dict(atlas=source,box=box,source_png=png.as_posix()))
        input_file=scratch/(Path(source).stem+'.png');image.save(input_file)
        folder=dest/Path(source).parent;folder.mkdir(parents=True,exist_ok=True)
        subprocess.run([str(tool),'-f','BC3_UNORM','-m','1','-y','-o',str(folder),str(input_file)],check=True,stdout=subprocess.DEVNULL)
        assert Image.open(dest/source).size==(w,h)
        print('Rebuilt native atlas',source,flush=True)
for name in ('icons.json','materials.json'):(dest/name).write_bytes((native/name).read_bytes())
(dest/'morematerials.json').write_text(json.dumps(dict(Materials=[],AtlasTextures=[],GlobalTextures=[])))
with open('work/faction-ui-icons.tsv','w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=('kind','civ','id','icon'),delimiter='\t',extrasaction='ignore');writer.writeheader();writer.writerows(bindings)
report=dict(bindings=bindings,native_slots={k:len(v) for k,v in slots.items()},atlas_regions=regions,shared_technology_art_differences=sorted(set(differences)),limitations=['Existing native icon slots/atlases carry source art while the companion is enabled; disable the companion for normal DE icons','BC3 atlas encoding is lossy; individual DDS pixels retain the resized source colors','Runtime rendering still needs confirmation'])
Path('outputs/faction-icon-ui-report.json').write_text(json.dumps(report,indent=2))
print(len(bindings),'bindings in existing native slots',report['native_slots'])
