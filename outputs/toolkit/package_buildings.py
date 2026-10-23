"""Package the optional building preview, run from the task root."""
from pathlib import Path
import csv,hashlib,json,shutil,struct,zlib
root=Path('outputs'); data_mod=root/'SWGB-DE-Buildings-Preview'
assets=root/'SWGB-DE-Assets'; local=Path.home()/'Games/Age of Empires 2 DE/76561198022514833/mods/local'
assert Path('work/building-audited.raw').read_bytes()==Path('work/de.raw').read_bytes()
mapping=list(csv.DictReader(open('work/building-graphic-mapping.tsv'),delimiter='\t'))
source={r['id']:r for r in csv.DictReader(open(root/'ef-graphics.tsv'),delimiter='\t')}
variants=0
for m in mapping:
    if int(m['slp'])<0:
        assert not m['filename']
        continue
    for folder,suffix in [('building-converted','_x1'),('building-converted4x','_x2')]:
        b=(Path('work')/folder/('swgb_'+m['source']+'.smx')).read_bytes()
        g=source[m['source']];assert b[:4]==b'SMPX'
        assert struct.unpack_from('<H',b,6)[0]==int(g['frames'])*int(g['angles'])
        dest=assets/'resources/_common/drs/graphics'/(m['filename'].replace('_x1',suffix)+'.smx')
        # The released troops/lasers must remain byte-identical.
        if dest.exists():assert dest.read_bytes()==b,str(dest)
        else:dest.write_bytes(b)
        target=local/assets.name/dest.relative_to(assets);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dest,target)
        assert target.read_bytes()==b
        variants+=1
raw=Path('work/building-mod.raw').read_bytes();co=zlib.compressobj(9,zlib.DEFLATED,-15);compressed=co.compress(raw)+co.flush()
assert zlib.decompress(compressed,-15)==raw
dest=data_mod/'resources/_common/dat/empires2_x2_p1.dat';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(compressed)
(data_mod/'info.json').write_text(json.dumps(dict(Title=data_mod.name,Author='Local SWGB port project',CacheStatus=0,Version='0.0.2-preview',Description='Optional test dataset. Requires SWGB-DE-Assets. Briton/Frank houses use imported prefab art, construction and damage fire. Native house stats and destruction remain. Includes source blaster trails.'),indent=2))
shutil.copytree(data_mod,local/data_mod.name,dirs_exist_ok=True)
assert (local/data_mod.name/dest.relative_to(data_mod)).read_bytes()==compressed
report=dict(status='Installed optional preview; not engine verified or released',version='0.0.2-preview',graphics=len(mapping),sprite_variants=variants,composite_parent_graphics=sum(int(m['slp'])<0 for m in mapping),native_gameplay_fields_unchanged=True,released_sprite_bytes_unchanged=True,dat_sha256=hashlib.sha256(compressed).hexdigest(),blaster_trail_ids=[2704,2705],source_trail_density=0.035,house_civs=[1,2],house_units=[70,463,464,465])
(root/'building-preview-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
