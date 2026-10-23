"""Audit direct source upgrade edges against raw/copy runtime identity assumptions.

The source master copy retains raw ID/base/class but copies the upgrade's copy
ID and other attributes. This report is not a full reachable research sequence.
"""
from pathlib import Path
from collections import Counter
import csv,json
from classic_force_rank import ranks
from classic_unit_ai_factory import unit_ai_type
from classic_unit_identity import sha
from classic_conversion_eligibility import EXCLUDED_IDS
from classic_attack_eligibility import catalog
from classic_target_model import ECONOMIC_IDS

ROOT=Path('work/classic-engine')


def ai(kind,cls,volley):
    return unit_ai_type(cls,volley) if kind in (70,80) else -1


def main():
    proof=json.loads((ROOT/'force-rank-validation.json').read_text())
    assert proof['passed'] and len(proof['copy_identity_probes'])==4
    rows={(int(r['civ']),int(r['slot'])):r for r in csv.DictReader((ROOT/'unit-identity.tsv').open(),delimiter='\t')}
    changes=[];unknown=[];counts=Counter();edges=set()
    ground_to_air,ground_sha=catalog()
    # Report potential predicate changes, not reachable combat outcomes: class,
    # stance, immunity and research guards may make a changed ID test irrelevant.
    id_tests={
        'conversion_exclusion':lambda uid:uid in EXCLUDED_IDS,
        'base_attack_target_exclusion':lambda uid:uid==696,
        'ground_to_air_override':lambda uid:uid in ground_to_air,
        'air_research_override':lambda uid:uid in (500,603),
        'tower_target_exclusion':lambda uid:uid==50,
        'soldier_action_exception':lambda uid:uid==109,
        'temple_victory_score':lambda uid:uid==104,
        'wonder_victory_score':lambda uid:uid==276,
        'economic_target_rank':lambda uid:uid in ECONOMIC_IDS,
    }
    for command in csv.DictReader((ROOT/'force-source/effects.tsv').open(),delimiter='\t'):
        if command['type']!='3':continue
        source,target=int(command['a']),int(command['b'])
        for civ in range(3):
            if (civ,source) not in rows or (civ,target) not in rows:
                unknown.append(dict(civ=civ,source=source,target=target,effect=int(command['effect'])))
                continue
            before,after=rows[civ,source],rows[civ,target]
            oldclass,newclass=int(before['source_class']),int(after['source_class'])
            oldtype,newtype=int(before['source_type']),int(after['source_type'])
            oldvolley,newvolley=int(before['source_volley_missile']),int(after['source_volley_missile'])
            beforeAI=ai(oldtype,oldclass,oldvolley)
            afterAI=ai(newtype,oldclass,newvolley)
            copiedAI=ai(newtype,newclass,newvolley)
            reasons=[]
            if oldclass!=newclass:reasons.append('retained_class_differs_from_copy_template')
            if afterAI!=copiedAI:reasons.append('factory_differs_using_copy_template_class')
            if beforeAI!=afterAI:reasons.append('new_unit_factory_differs_from_existing_factory')
            if ranks(source,target)!=ranks(target,target):reasons.append('rank_depends_on_raw_id')
            for name,test in id_tests.items():
                if test(source)!=test(target):reasons.append('raw_id_test_'+name)
            counts['mapped_applications']+=1;edges.add((civ,source,target))
            if reasons:
                counts.update(reasons)
                changes.append(dict(civ=civ,effect=int(command['effect']),ordinal=int(command['command']),
                    source=source,target=target,source_name=before['source_name'],target_name=after['source_name'],
                    retained_class=oldclass,copy_class=newclass,old_type=oldtype,new_type=newtype,
                    factory_before=beforeAI,factory_after=afterAI,copy_template_factory=copiedAI,reasons=reasons))
    report=dict(counts=dict(counts),unique_mapped_edges=len(edges),changes=changes,unmapped=unknown,
                source_copy_evidence_sha256=sha(ROOT/'force-rank-validation.json'),
                inputs={str(p):sha(p) for p in (ROOT/'unit-identity.tsv',ROOT/'force-source/effects.tsv')},
                ground_to_air_sha256=ground_sha,
                tool_sha256=sha(Path(__file__)),installed=False,full_behavior_parity=False,
                limitations=['Direct DAT upgrade edges, including unreachable/editor-only units.',
                             'Changed raw-ID tests are potential differences; other predicate guards are not evaluated here.',
                             'Does not yet model upgrade chains, player notifications or existing UnitAI persistence.',
                             'DE raw/copy getter behavior still needs native verification.'])
    (ROOT/'upgrade-identity-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(counts=report['counts'],unique_edges=len(edges),unmapped=len(unknown)),indent=2))


if __name__=='__main__':main()
