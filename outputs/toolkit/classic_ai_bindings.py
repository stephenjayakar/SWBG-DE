"""Reviewed SWGB symbol bindings, validated against source DAT exports."""
import csv
import json
import re
from pathlib import Path
from collections import defaultdict


def rows(name):
    return list(csv.DictReader(Path('work/faction-source', name+'.tsv').open(), delimiter='\t'))


def tech_bindings(civ):
    # Original AI aliases often predate the localized EF technology names.
    pairs = '''
    avail-awing:9 aa-battery:731 aaretrofit:568 adv-flight-school:76 adv-generator:166
    adv-harvesting:136 adv-power-pack:81 adv-propulsion:184 adv-redesign:168
    adv-scanners:186 adv-torpedoes:868 advparticlecannon:978 altered-bargains:194
    amplify-shield-proj:181 armor-plating:77 artusiancrystals:976 assembly-droids:196
    astromechs:663 attack-programming:139 automated-processes:206 aux-power-cells:869
    bacta-tank:501 basic-armor:65 basic-training:33 battle-armor:137
    battlefield-scanners:668 beamdrill-metal:171 beamdrill-nova-mining:149
    beast-training:797 black-market-components:671 bothan-spies:62 bunkerbusters:931
    chain-lightning:660 cloning:127 conflagrine:870 cooling-sleeves:74
    creature-training:145 cruboost:583 dexterity:205 diligence:574 disruptors:986
    drafted-labor:72 droidupg:577 durasteel:173 effbldgs:571 elevation-tracking:63
    enh-dexterity:796 enh-fusion-cutter:161 enlarged-bomb-hold:70 evac:665
    explosive-yields-inc:202 external-sensor-pod:75 faith-in-the-force:155
    farseein-binoculars:201 flight-school:71 force-influence:156 force-strong:157
    forest-vision:148 fortressworlds:977 fusion-cutter:160 fusion-extractor:132
    galactic-banking:190 galactic-trade-comm:193 galsenhb:580 genetics:83 geoengnr:576
    goonga-armor:167 gren-reload:535 gunship-lasers:667 hailfire-missiles:670
    harvesting:135 heavy-armor:67 heavy-beamdrill-metal:172 heavy-fusion-cutter:162
    heavy-plating:68 holonet:61 homing-sensors:178 huntressmastery:1153 huntresstrain:988
    hutt-endorsement:188 hvy-beamdrill-nova:150 hvy-weapons-engineers:179 indoctrination:867
    integrated-rgefinder:203 ion-accelerator:174 irrigation:134 jedi-agility:151
    jedi-concentration:152 jedi-meditation:500 jedi-mind-trick:159 jedi-perception:158
    jedi-stamina:153 jedi-strength:154 jetpacks:143 kamclonr:579 kamino-refit:582
    light-armor:79 light-plating:64 lighter-armor:198 lighter-material:78
    macrobinoculars:197 magdetenforcers:1154 medium-plating:80 newjediorder:980
    nova-fusion-extractor:669 optimized-motivator:129 permacite-plating:180 phased-pulse:673
    plasma-detonators:664 portable-scanners:199 potent-plasma:662 power-calibrator:175
    presidium:141 primary-focus-coils:66 pwrcshld:572 rebel-mechanics:147 redesigned-specs:183
    redoubled-efforts:185 reinforced-frames:146 resilience:932 rotation-bearings:176
    salvcomponents:1152 self-regeneration:133 sensor-array:130 sensor-beacon:126
    sgtbysgt:581 shield-mods:73 stimpacks:1219 stimulants:82 strengthened-frames:144
    strgassy:573 strgsupr:569 suprshld:570 targetting-sensors:69 taxation:138
    tougher-armor:204 tracking-computer:177 transport-capability:164 upgraded-generators:163
    upgraded-motivator:128 upgrmedd:578 veterancy:983 wookiee-ingenuity:169 wookiee-mechanics:170
    neimoidian-endorse:189 insider-trading:192 market-control:195 piracy:672 confalli:575
    '''
    mapping = {'rt-'+k: int(v) for k,v in (p.split(':') for p in pairs.split())}
    techs = {int(r['id']):r for r in rows('techs')}
    # Per-civilization aliases must resolve to that faction's research, not an AoE id.
    suffix = {1:'E',3:'R'}[civ]
    stems = dict(laser_2='UNIT-TTRP',laser_3='UNIT-THTP',laser_4='UNIT-TMGT',
                 mounted_2='UNIT-THAN',mounted_3='UNIT-TAAT',missile_troop_2='UNIT-THMS',
                 single_mech_2='UNIT-MH1T',dual_mech_2='UNIT-MH2T',multi_mech_2='UNIT-MH3T',
                 artillery_2='UNIT-HART',missile_launcher_2='UNIT-HHML',ram_2='UNIT-HHRM',
                 bomber_2='UNIT-AHBM',bomber_3='UNIT-AABM',fighter_2='UNIT-AHFT',fighter_3='UNIT-AAFT',
                 boat_laser_2='BOAT-SSCT',boat_laser_3='BOAT-SASC',boat_artillery_2='BOAT-SASP',
                 boat_cutlaser_2='BOAT-SFLS',boat_missile_2='BOAT-SHMS',jedi_2='UNIT-JKNT')
    for alias,stem in stems.items():
        matches = [tid for tid,r in techs.items() if r['name']=='UPGRADE-'+stem+suffix and int(r['civ'])==civ]
        assert len(matches)==1, (alias,matches)
        mapping['ut-'+alias.replace('_','-')] = matches[0]
    # CC_shipyard.per's historical "grenade" alias upgrades the Monitor line.
    mapping['ut-boat-grenade-2'] = {1:704,3:706}[civ]
    unique = '''adv-missile-turret:447 adv-turret:481 airspeeder:476 dark-trooper:472
    heavy-wall:483 medium-turret:480 shield-wall:484 scramjets:981 newclassmod:982
    spiritichor:985 berserker:477 defiler:674 destroyer-droid:113 faamba-shield-gen:474
    geonosian-flyer:794 gladiatordroid:989 jedi-starfighter:533 magnaguard:534
    peopleoftrees:966 riot-trooper:866 royal-knight:475 shadowtrooper:979
    skispeeder:925 vwing:984'''
    mapping.update({'ut-'+k:int(v) for k,v in (p.split(':') for p in unique.split())})
    assert all(t in techs for t in mapping.values())
    return mapping


def faction_units(civ, source_units):
    suffix = {1:'E',3:'R'}[civ]
    stems = {'boat-laser2':'BOAT-SSCT','boat-transport':'BOAT-STRN',
             'unit-bomber1':'UNIT-ABOM','unit-bomber2':'UNIT-AHBM',
             'unit-jedi4':'UNIT-JMST','unit-medic':'UNIT-OMED',
             'unit-mounted1':'UNIT-TANI','unit-mounted2':'UNIT-THAN',
             'unit-packed1':'UNIT-GBLC','unit-unpacked1':'UNIT-GUBLC',
             'unit-grentrp':'UNIT-TGRE','unit-bounty':'UNIT-GBNT','unit-air-cruiser':'UNIT-ACRU'}
    # SWGB IDs, like every binding here (931 and the bounty/medic/packed units resolved below sit in
    # DE's reserved group range 900-999). port_classic_ai.py maps unit symbols to DE IDs on output.
    result = {'boat-worker':13,'unit-cargosp':931,'unit-nghtbstm':5235,'unit-nghthntr':4172}
    for alias,stem in stems.items():
        hits = [i for i,r in source_units.items() if r['name']==stem+suffix and i<1100]
        assert len(hits)==1,(alias,hits)
        result[alias]=hits[0]
    return result


def unit_bindings():
    """Return real SWGB groups plus generic building and worker aliases."""
    rms = {k.lower(): int(v) for k,v in re.findall(r'#const\s+(\S+)\s+(\d+)',
           Path('work/extracted/gamedata_x2/54000.bin').read_text())}
    source_units = {int(r['id']):r for r in rows('units') if r['civ']=='1'}
    groups = defaultdict(list)
    for r in csv.DictReader(Path('work/original-ai/source-lines.tsv').open(),delimiter='\t'):
        key = r['name'].lower()
        if not key.startswith(('unit-','bldg-','boat-','siege-','gaia-','uu-')):
            continue
        uid = int(r['unit'])
        if uid not in groups[key]: groups[key].append(uid)
    raw = {'bldg-aabattery':1869,'bldg-dropanim':319,'bldg-dropcarbon':562,'bldg-dropchow':68,
           'bldg-dropmetal':584,'bldg-dropnova':323,'bldg-farm':50,'bldg-gate':487,
           'bldg-govtctr':82,'bldg-main':109,'bldg-missile1':236,'bldg-missile2':196,
           'bldg-monument':276,'bldg-powercore':12,'bldg-prefab':70,'bldg-resctr':209,
           'bldg-shldgen':335,'bldg-spaceport':84,'bldg-trainair':317,'bldg-trainboat':45,
           'bldg-trainheavy':49,'bldg-trainjedi':104,'bldg-trainmech':101,'bldg-traintrooper':87,
           'bldg-turret1':79,'bldg-turret2':234,'bldg-turret3':235,'bldg-warctr':103,
           'bldg-barrier1':117,'bldg-barrier2':155,'bldg-barrier3':195,'unit-worker':83}
    aliases = {'unit-air-cruiser':'unit-aircruiser-line','unit-bounty':'unit-bounty-line',
               'unit-grentrp':'unit-grenade-line'}
    for alias,base in aliases.items(): groups[alias] = list(groups[base])
    # Legacy alias retained by CC_heavy-weapons but absent from EF's UnitLines.
    # Compatibility interpretation: the Gungan Cruiser/Advanced Cruiser pair.
    # This unresolved original alias is explicitly recorded in ORIGINAL-AI.md.
    groups['sub-artillery-line']=[818,805]
    assert source_units[818]['name']=='BOAT-SSSHG' and source_units[805]['name']=='BOAT-SASPG'
    # SWGB's UNIT-WORKER counts all job/gender variants; DE does not know the
    # source job ids. Keep training on 83, but provide a complete counting group.
    current=list(csv.DictReader(Path('work/original-ai/current-dat/units.tsv').open(),delimiter='\t'))
    groups['unit-worker-count-line']=sorted({int(r['id']) for r in current
        if r['civ'] in ('1','2') and r['class']=='4' and r['type']=='70'})
    assert 83 in groups['unit-worker-count-line']
    # Native DE soldier/warboat classes differ from SWGB (notably aircraft).
    # These total-count predicates can use native unit-line accounting without
    # relying on DE's tactical class pools. Attack/defend counts also depend on
    # live group membership and remain separate controller work.
    from classic_air_model import GROUND_CLASSES
    source_traits={int(r['unit']):int(r['trait']) for r in rows('compat-units') if r['civ']=='1'}
    present={int(r['id']) for r in current if r['civ'] in ('1','2')}
    groups['source-ground-soldier-line']=sorted(uid for uid,r in source_units.items()
        if uid in present and int(r['class']) in GROUND_CLASSES)
    groups['source-warboat-line']=sorted(uid for uid,r in source_units.items()
        if uid in present and source_traits[uid]&2 and int(r['class']) in (11,13,15,16,37,38,39,40))
    assert 773 not in groups['source-ground-soldier-line']  # TIE Fighter
    assert all(groups[key] for key in ('source-ground-soldier-line','source-warboat-line'))
    # All age variants of generic buildings are the same AI building identity.
    upgrades = defaultdict(set)
    for row in rows('effects'):
        if row['type']=='3': upgrades[int(row['a'])].add(int(row['b']))
    def closure(start):
        result={start};todo=[start]
        while todo:
            uid=todo.pop()
            for other in upgrades[uid]-result:
                if other in source_units and source_units[other]['type']==source_units[start]['type']:
                    result.add(other);todo.append(other)
        return [start]+sorted(result-{start})
    for alias,uid in raw.items():
        if alias.startswith('bldg-') and not re.search(r'\d$',alias): groups[alias]=closure(uid)
    for alias in ('bldg-barrier1','bldg-barrier2','bldg-barrier3'):
        assert raw[alias]==rms[alias]
    return raw, dict(groups), rms, source_units


if __name__=='__main__':
    root=Path('work/original-ai')
    raw,groups,rms,units=unit_bindings()
    for faction,civ in [('empire',1),('rebel',3)]:
        symbols=json.loads((root/(faction+'-symbols.json')).read_text())
        known={**tech_bindings(civ),**raw,**groups}
        missing=[s for s in symbols if s.startswith(('rt-','ut-','unit-','boat-','bldg-','gaia-')) and s not in known and s not in ('unit-type-count','unit-type-count-total')]
        print(faction,'missing',missing)
    print('groups',len(groups))

