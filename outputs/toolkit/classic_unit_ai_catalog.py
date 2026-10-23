"""Read constructor vtables and combat dispatch directly from the pinned source.

The symbol header only locates constructors; instructions and table pointers
come from the installed executable. This is not a runtime UnitAI implementation.
"""
from pathlib import Path
import hashlib
import json
import re
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86 import X86_OP_MEM,X86_OP_IMM,X86_REG_ESI
from classic_engine_oracle import Oracle,SOURCE_SHA

SYMBOLS=Path('work/efpatch/cheatdll/src/idb/idb_functions.h')
TYPES=('UnitAIModule','TribeHuntedAnimalUnitAIModule','TribeElephantUnitAIModule',
       'TribeLionUnitAIModule','TribeCivilianUnitAIModule','TribeMedicUnitAIModule',
       'TribePriestUnitAIModule','TribeTradeShipUnitAIModule','TribeTransportShipUnitAIModule',
       'TribeFishingShipUnitAIModule','TribeSoldierUnitAIModule','TribeArtifactUnitAIModule',
       'TribeTowerUnitAIModule','TribeSiegeUnitAIModule','TribeBuildingUnitAIModule')
ATTACK_KINDS={0x41C530:0,0x5B8A90:1,0x5B7CD0:2,0x5B6E70:3,0x5B4B60:4,
              0x5B8180:5,0x5B2F80:6,0x5B28F0:7,0x5B2FB0:8}
NEUTRAL_KINDS={0x5B2910:0,0x5B7D70:1,0x5B4D80:2,0x5B8440:3,0x5B2FB0:4}


def source_catalog():
    oracle=Oracle();dis=Cs(CS_ARCH_X86,CS_MODE_32);dis.detail=True
    rows=[]
    text=SYMBOLS.read_text()
    for index,name in enumerate(TYPES):
        pattern=r'const '+name+'__'+name+r'\).*?0x([0-9A-F]+);'
        matches=re.findall(pattern,text)
        assert len(matches)==1,(name,matches)
        constructor=int(matches[0],16)
        candidates=[]
        for ins in dis.disasm(bytes(oracle.cpu.mem_read(constructor,0x500)),constructor):
            if ins.mnemonic=='mov' and len(ins.operands)==2:
                a,b=ins.operands
                if a.type==X86_OP_MEM and a.mem.base==X86_REG_ESI and a.mem.disp==0 and b.type==X86_OP_IMM:
                    if 0x650000<=b.imm<0x700000:candidates.append(b.imm)
            if ins.mnemonic=='ret':break
        assert len(candidates)==1,(name,candidates)
        table=candidates[0]
        attack,neutral,convert=(oracle.read(table+off) for off in (0x4C,0x50,0xC0))
        assert attack in ATTACK_KINDS and neutral in NEUTRAL_KINDS and convert in (0x408B00,0x5B48E0)
        rows.append(dict(type=index,name=name,constructor=constructor,vtable=table,attack=attack,
                         neutral=neutral,convert=convert,attack_kind=ATTACK_KINDS[attack],
                         neutral_kind=NEUTRAL_KINDS[neutral],can_convert=convert==0x5B48E0))
    return rows


def main():
    rows=source_catalog()
    report=dict(source_sha256=SOURCE_SHA,symbols_sha256=hashlib.sha256(SYMBOLS.read_bytes()).hexdigest(),
                tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),types=rows,
                installed=False,full_behavior_parity=False,
                limitations=['Constructor stores and virtual dispatch only; no initialization or behavior execution.'])
    path=Path('work/classic-engine/unit-ai-catalog.json');path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',len(rows),'source UnitAI tables;',len({r['attack'] for r in rows}),'attack routines;',
          len({r['neutral'] for r in rows}),'neutrality routines;',len({r['convert'] for r in rows}),'conversion routines')


if __name__=='__main__':main()
