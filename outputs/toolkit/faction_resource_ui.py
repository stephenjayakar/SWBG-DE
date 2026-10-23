"""Port source resource symbols into existing DE UI slots without other changes.

Preserve compressed blocks outside the eight resource regions byte for byte.
Use existing mod atlases when present, otherwise DE's original atlas.
"""
from pathlib import Path
import argparse, hashlib, json, struct, subprocess
from PIL import Image, ImageChops, ImageStat, ImageDraw

cli=argparse.ArgumentParser()
cli.add_argument('--base',type=Path,default=Path('outputs/SWGB-DE-Factions-Draft'))
cli.add_argument('--root',type=Path,default=Path('work/worker-ui-repair/patch'))
args=cli.parse_args()
scratch=Path('work/worker-ui-repair');native=Path(r'E:/SteamLibrary/steamapps/common/AoE2DE/widgetui')
archive=Path(r'E:/GOG Games/Star Wars - Galactic Battlegrounds/Game/Data')
order={'interfac.drs':0,'interfac_x1.drs':1,'interfac_x2.drs':2}
entries=[r for r in json.loads(Path('outputs/archive-manifest.json').read_text())
         if r['id']==50731 and r['ext']=='slp' and r['archive'].lower() in order]
entry=max(entries,key=lambda r:order[r['archive'].lower()])
with (archive/entry['archive']).open('rb') as f:f.seek(entry['offset']);data=f.read(entry['size'])
slp=scratch/'resource-icons.slp';slp.write_bytes(data)
subprocess.run(['javac','-cp','work/smx-workshop/Export/SMX Workshop.jar;work/smx-workshop',
    '-d','work/smx-workshop','outputs/toolkit/RenderInterfaceSheet.java'],check=True)
pngdir=scratch/'resource-icons'
subprocess.run(['java','-cp','work/smx-workshop/Export/SMX Workshop.jar;work/smx-workshop',
    'RenderInterfaceSheet',str(slp),str(pngdir),'work/extracted/interfac_x2/50500.bin'],check=True)
# Original sheet 50731: blue Carbon, purple Ore, orange Food, green Nova.
frames={'ResourceWood':0,'ResourceStone':1,'ResourceFood':2,'ResourceGold':3}
materials=json.loads((native/'materials.json').read_text())
atlas=next(r['AtlasDef'] for r in materials['AtlasTextures'] if r['AtlasDef']['Name']=='ingamepanels')
paint=[]
for texture in atlas['Textures']:
    ref=texture['RefName'];base=ref.removesuffix('Transparent')
    if base not in frames:continue
    original=Image.open(pngdir/f'{frames[base]}.png').convert('RGBA')
    template=(native/texture['FileName']).read_bytes();w,h=Image.open(native/texture['FileName']).size
    image=original.resize((w,h),Image.Resampling.NEAREST)
    # Keep PNG inputs as PNG. DDS inputs retain the existing port convention.
    header=bytearray(128);header[:4]=b'DDS '
    struct.pack_into('<I',header,4,124)
    struct.pack_into('<II',header,12,h,w)
    struct.pack_into('<I',header,108,0x1000)
    struct.pack_into('<I',header,8,0x2100f);struct.pack_into('<I',header,20,w*4)
    struct.pack_into('<I',header,28,1)
    struct.pack_into('<8I',header,76,32,0x41,0,32,0xff,0xff00,0xff0000,0xff000000)
    dest=args.root/'widgetui'/texture['FileName'];dest.parent.mkdir(parents=True,exist_ok=True)
    if template[:8]==b'\x89PNG\r\n\x1a\n':image.save(dest,format='PNG')
    else:dest.write_bytes(header+image.tobytes())
    assert Image.open(dest).convert('RGBA').tobytes()==image.tobytes()
    paint.append((texture,original))
assert len(paint)==8
regions=[]
for source in sorted({atlas[k] for k in ('SDSource','HDSource','UHDSource','DefaultSource') if k in atlas}):
    input_path=args.base/'widgetui'/source
    if not input_path.exists():input_path=native/source
    before=input_path.read_bytes()
    assert before[:4]==b'DDS '
    if before[84:88]==b'DXT5':header_size,codec=128,'BC3_UNORM'
    else:
        assert before[84:88]==b'DX10' and struct.unpack_from('<I',before,128)[0]==98
        header_size,codec=148,'BC7_UNORM'
    assert struct.unpack_from('<I',before,28)[0]==1
    im=Image.open(input_path).convert('RGBA');w,h=im.size
    assert len(before)==header_size+((w+3)//4)*((h+3)//4)*16
    boxes=[];touched=set()
    for texture,original in paint:
        box=tuple(round(float(texture[k])*size+adj) for k,size,adj in (
            ('imageTLX',w,-.5),('imageTLY',h,-.5),('imageBRX',w,.5),('imageBRY',h,.5)))
        x,y,right,bottom=box;assert 0<=x<right<=w and 0<=y<bottom<=h
        resized=original.resize((right-x,bottom-y),Image.Resampling.NEAREST)
        im.paste(resized,(x,y));boxes.append((box,resized))
        for by in range(y//4,(bottom+3)//4):
            for bx in range(x//4,(right+3)//4):touched.add(by*((w+3)//4)+bx)
    stage=scratch/Path(source).parent;stage.mkdir(parents=True,exist_ok=True)
    im.save(stage/'ingamepanels.png')
    subprocess.run([str(native.parent/'Tools_Builds/texconv.exe'),'-f',codec,'-m','1','-y',
        '-o',str(stage),str(stage/'ingamepanels.png')],check=True,stdout=subprocess.DEVNULL)
    encoded=(stage/'ingamepanels.dds').read_bytes();assert len(encoded)==len(before)
    merged=bytearray(before)
    for block in touched:
        offset=header_size+16*block;merged[offset:offset+16]=encoded[offset:offset+16]
    dest=args.root/'widgetui'/source;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(merged)
    # Exact encoded-byte collateral audit; decoding untouched blocks is identical.
    for block in range((len(before)-header_size)//16):
        if block not in touched:
            off=header_size+block*16;assert merged[off:off+16]==before[off:off+16]
    assert merged[:header_size]==before[:header_size]
    read=Image.open(dest).convert('RGBA')
    for (box,resized),(texture,_) in zip(boxes,paint):
        # RGB under zero alpha is invisible and not preserved by BC compression.
        # Check visible error composited over both dark and bright UI surfaces.
        error=0
        for color in ((0,0,0,255),(255,255,255,255)):
            back=Image.new('RGBA',resized.size,color)
            actual=Image.alpha_composite(back,read.crop(box))
            expected=Image.alpha_composite(back,resized)
            error=max(error,max(ImageStat.Stat(ImageChops.difference(actual,expected)).mean))
        # The smallest SD glyph is 33px and BC3 mixes its high-contrast indexed
        # colors within 4px blocks. Bound mean visible error to <5% per channel.
        assert error<12.75,(source,texture['RefName'],error)
        regions.append(dict(atlas=source,ref=texture['RefName'],box=box,max_mean_channel_error=error))
    print(source,':',len(touched),'patched blocks; all other bytes unchanged')
preview=Image.new('RGB',(640,116),(35,35,35));draw=ImageDraw.Draw(preview)
for i,(name,frame) in enumerate(frames.items()):
    im=Image.open(pngdir/f'{frame}.png').convert('RGBA').resize((56,56),Image.Resampling.NEAREST)
    preview.paste(im,(i*160+10,15),im);draw.text((i*160+10,85),{'ResourceWood':'Carbon','ResourceStone':'Ore','ResourceFood':'Food','ResourceGold':'Nova'}[name],fill='white')
preview.save('outputs/resource-hud-preview.png')
Path('outputs/resource-ui-validation.json').write_text(json.dumps(dict(source=entry,
    source_sha256=hashlib.sha256(data).hexdigest(),frame_bindings=frames,individual_pixels_exact=True,
    untouched_atlas_blocks_exact=True,regions=regions,engine_verified=False),indent=2))
