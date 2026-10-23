from pathlib import Path
import re,json,hashlib
script=Path('work/faction-package/resources/_common/xs/swgb_factions.xs').read_text()
exe=Path(r'E:\SteamLibrary\steamapps\common\AoE2DE\AoE2DE_s.exe').read_bytes()
functions=sorted(set(re.findall(r'\b(xs\w+)\(',script)))
missing=[f for f in functions if f.encode() not in exe and f.encode('utf-16le') not in exe]
assert not missing,missing
maps=json.loads(Path('outputs/faction-map-report.json').read_text())['maps']
for r in maps:
 p=Path('work/faction-package/resources/_common/random-map-scripts')/r['file']
 assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'],r['file']
 assert p.read_text().count('#includeXS swgb_factions.xs')==1
print('Native executable contains all',len(functions),'XS API names; 20 map hashes/includes match. This is not an XS compile test.')
