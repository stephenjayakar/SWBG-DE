"""Read installed source DLL resources as data and stage faction English UI strings."""
import ctypes,csv,json
from faction_language_ids import text_ids
from ctypes import wintypes
from pathlib import Path
GAME=Path(r'E:\GOG Games\Star Wars - Galactic Battlegrounds\Game')
kernel=ctypes.WinDLL('kernel32',use_last_error=True);user=ctypes.WinDLL('user32',use_last_error=True)
kernel.LoadLibraryExW.argtypes=[wintypes.LPCWSTR,wintypes.HANDLE,wintypes.DWORD];kernel.LoadLibraryExW.restype=wintypes.HMODULE
kernel.FreeLibrary.argtypes=[wintypes.HMODULE]
user.LoadStringW.argtypes=[wintypes.HINSTANCE,wintypes.UINT,wintypes.LPWSTR,ctypes.c_int]
strings={};buffer=ctypes.create_unicode_buffer(32768)
for filename in ('language.dll','language_x1.dll','language_x2.dll'):
    handle=kernel.LoadLibraryExW(str(GAME/filename),None,2) # LOAD_LIBRARY_AS_DATAFILE: no DLL code executes.
    if not handle:raise ctypes.WinError(ctypes.get_last_error())
    try:
        for sid in range(65536):
            if user.LoadStringW(handle,sid,buffer,len(buffer)):strings[sid]=buffer.value
    finally:kernel.FreeLibrary(handle)
def read(name):return list(csv.DictReader(open('work/faction-source/'+name+'.tsv'),delimiter='\t'))
units={(int(x['civ']),int(x['id'])):x for x in read('units')}
techs={int(x['id']):x for x in read('techs')}
output={890001:'Galactic Empire',890002:'Rebel Alliance',
        898001:'Force Conversion',
        898002:'Force Conversion: select this command, then an enemy target. Right-click enemies for lightsaber combat. Experimental DE ability: 15 game-second recharge.'};missing=[]
for row in read('language-ids'):
    source_civ=int(row['civ']);uid=int(row['id']);kind=row['kind']
    name_id=int(row['name']);description_id=int(row['description']);help_id=int(row['help'])-79000
    if kind=='unit':
        civ={0:0,1:1,3:2}[source_civ];unit=units[(source_civ,uid)];civ_index=max(source_civ-1,0)
        # AGE GetUnitName and EF langdll hooks resolve these names at runtime.
        # uid is the SWGB unit ID (931 = UNIT-OCSPEM, now DE 1628): it selects source DLL strings and the DAT's
        # string IDs stay derived from it, so it is deliberately not mapped through
        # reserved_unit_ids.de_unit_id even though the DE unit now lives outside 900-999.
        dynamic=None
        if int(unit['class'])==58:dynamic=(100000+civ_index+6*(name_id-5001))&65535
        elif uid in (30,31,104,3593,3594,3595):dynamic=(99917+civ_index)&65535
        elif uid in (931,434):dynamic=({931:99957,434:99937}[uid]+civ_index)&65535
        if dynamic is not None:name_id=dynamic;description_id=(dynamic+1000)&65535;help_id=(dynamic+21000)&65535
        ids=text_ids(kind,civ,uid)
        fallback=unit['name'];verb='Build' if unit['type']=='80' else 'Create'
    else:
        ids=text_ids(kind,-1,uid);fallback=techs[uid]['name'];verb='Research'
    name=strings.get(name_id,'')
    if not name:missing.append(dict(kind=kind,civ=source_civ,id=uid,field='name',source_string=name_id));name=fallback
    description=strings.get(description_id,'') or f'{verb} {name}'
    help_text=strings.get(help_id,'')
    if not help_text:missing.append(dict(kind=kind,civ=source_civ,id=uid,field='help',source_string=help_id));help_text=f'{verb} <b>{name}<b> (<cost>)'
    for sid,value in zip(ids,(name,description,help_text)):
        if sid in output and output[sid]!=value:raise ValueError(('String collision',sid))
        output[sid]=value.replace('\r\n','\n').replace('\r','\n')
from faction_defense_ui import defense_strings
output.update(defense_strings())
import faction_civs
output.update(faction_civs.description_strings(strings))
root=Path('work/faction-package');folder=root/'resources/en/strings/key-value';folder.mkdir(parents=True,exist_ok=True)
with (folder/'key-value-modded-strings-utf8.txt').open('w',encoding='utf-8') as f:
    for sid,text in sorted(output.items()):f.write(f'{sid} {json.dumps(text,ensure_ascii=False)}\n')
data=root/'resources/_common/dat';data.mkdir(parents=True,exist_ok=True)
# Full entries with native slot data_name (DE 185872 DLC gate); see faction_civs.py.
(data/'civilizations.json').write_text(json.dumps(faction_civs.civilizations(),indent=2))
report={'strings':len(output),'unresolved_source_fields':missing,'status':'Staged only; civilization picker, text markup and technology-tree UI not engine verified'}
Path('outputs/faction-ui-report.json').write_text(json.dumps(report,indent=2))
print('Staged',len(output),'strings;',len(missing),'source fields used explicit fallbacks')
