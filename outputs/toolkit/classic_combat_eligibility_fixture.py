"""Test-only source observations connecting eligibility to the combat pipeline.

The compiled host invokes the actual XS predicates; this supplies fixture world
state and compares each gate with original executable results before aggregation.
"""
from dataclasses import fields
import random
import struct
from classic_attack_eligibility import catalog,generate_catalog
from classic_soldier_eligibility import Soldier
from classic_soldier_eligibility_oracle import SoldierEligibilityOracle
from classic_conversion_eligibility import Conversion
from classic_conversion_eligibility_oracle import ConversionEligibilityOracle
from classic_unit_ai_factory_oracle import UnitAIFactoryOracle

XS_NAMES=('classic_attack_eligibility.xs','classic_soldier_eligibility.xs','classic_conversion_eligibility.xs')


def field_values(value):
    result=[]
    for f in fields(value):
        x=getattr(value,f.name)
        result.append(struct.unpack('<I',struct.pack('<f',x))[0] if f.type is float else int(x))
    return result


def host_reader(source_types=False):
    members=[('s_'+f.name,f.type) for f in fields(Soldier)]+[('c_'+f.name,f.type) for f in fields(Conversion)]
    declarations='\n'.join(('uint32_t' if t is float else 'int')+' '+name+';' for name,t in members)
    reads='>>'.join(name for name,_ in members)
    arguments=[('gateFloat('+name+')' if t is float else name) for name,t in members]
    s=arguments[:21];c=arguments[21:]
    motion=','.join(s[12:]+[s[8]])
    if source_types:
        return ('float gateFloat(uint32_t b){float f;std::memcpy(&f,&b,4);return f;}\n'
                'Capabilities readSourceEligibility(){int kind,ownState,held,volley;'+declarations+
                '\nstd::cin>>kind>>ownState>>held>>volley>>'+reads+';\n'
                'classicCombatSetActorTemplate(s_attacker_class,volley,ownState,held,1,70);\n'
                'if(classicCombatActorKind!=kind) throw std::runtime_error("Source factory dispatch mismatch");\n'
                'classicAttackSoldierSetMotion('+motion+');\n'
                'bool attack=classicCombatCanAttack('+','.join(s[1:12])+');\n'
                'classicConvertSetPermissions('+','.join(c[10:])+');\n'
                'bool convert=classicCombatCanConvert('+','.join(c[1:10])+');\n'
                'return Capabilities{attack,convert,classicCombatActorHasAI()};}\n')
    return ('float gateFloat(uint32_t b){float f;std::memcpy(&f,&b,4);return f;}\n'
            'Capabilities readSourceEligibility(){int kind,ownState,held;'+declarations+
            '\nstd::cin>>kind>>ownState>>held>>'+reads+';\n'
            'classicAttackSoldierSetMotion('+motion+');\n'
            'bool attack=false;\n'
            'if(kind==0) attack=classicAttackBase('+','.join(s[:6])+');\n'
            'if(kind==1) attack=classicAttackBuilding('+','.join(s[:6])+');\n'
            'if(kind==2) attack=classicAttackTower('+','.join(s[:11]+['ownState'])+');\n'
            'if(kind==3) attack=classicAttackSoldier('+','.join(s[:12])+');\n'
            'if(kind==4) attack=classicAttackPriest('+','.join(s[:11]+['held'])+');\n'
            'if(kind==5) {classicAttackSiegeSetState(ownState,1);attack=classicAttackSiege('+','.join(s[:12])+');}\n'
            'if(kind==6 || kind==7) attack=classicAttackNullable('+','.join(s[:7])+');\n'
            'if(kind==8) attack=classicAttackNever();\n'
            'classicConvertSetPermissions('+','.join(c[10:])+');\n'
            'bool convert=kind==4 && classicCanConvert('+','.join(c[:10])+');\n'
            'return Capabilities{attack,convert};}\n')


class EligibilityFixtures:
    def __init__(self,source_types=False):
        self.ids,self.sha=catalog()
        self.attack=SoldierEligibilityOracle()
        self.convert=ConversionEligibilityOracle()
        self.rng=random.Random(0x5B48E0592430)
        self.counts={str(i):0 for i in range(9)}
        self.outcomes={}
        self.source_types=source_types
        self.factory=UnitAIFactoryOracle() if source_types else None
        self.factory_types={}
        if source_types:self.counts['-1']=0

    def prelude(self):
        return generate_catalog(self.ids,self.sha)

    def definition(self,army_member=False):
        r=self.rng
        result=dict(kind=r.randrange(9),cls=r.choice((5,7,8,9,18,32,34,35,36,43,48,50,51,64)),
                    id=r.choice((1,50,104,109,500,603,*self.ids)),held=r.choice((0,0,57)),
                    ownState=r.choice((1,2,2,3)),flag=r.choice((0,0,0,1)),
                    stance=r.randrange(4),last=r.choice((600,600,601)),order=r.choice((0,701,711,733)),
                    on=r.randrange(2),patrol=r.randrange(2),range=r.uniform(0,15),
                    action=r.choice((-1,-1,124,125)),master=bool(r.randrange(2)),padawan=r.randrange(5)==0,
                    force=r.choice((50,99.9,100,120)),r31=r.randrange(2),r67=r.choice((0,1,1)),
                    r27=r.randrange(2),r87=r.randrange(2))
        if self.source_types:
            # Source combat evaluation dereferences own UnitAI on its low-damage
            # conversion branch. Keep that observed precondition here; no-AI
            # enemies/targets and the separate raw-capability tests remain.
            classes=(1,4,5,6,7,8,9,10,11,12,14,17,21,28,34,35,36,43,48,50,51,54,58,59,60,64)
            result['cls']=r.choice(classes if army_member else (3,*classes))
            result['volley']=r.choice((-1,0,773))
            key=(result['cls'],result['volley'])
            if key not in self.factory_types:self.factory_types[key]=self.factory.select(*key)[0]
            result['ai_type']=self.factory_types[key]
            result['kind']=-1 if result['ai_type']==-1 else self.factory.catalog[result['ai_type']]['attack_kind']
        return result

    def pair(self,a,v,x,y):
        r=self.rng
        target_type=80 if y['building'] else 70
        x,y=x['eligibility'],y['eligibility']
        kind=x['kind']
        s=Soldier(attacker_class=x['cls'],attacker_id=x['id'],target_class=y['cls'],target_id=y['id'],
                  invisible=r.randrange(5)==0,resource31=x['r31'],owner_id=1 if a.uid<100 else 2,
                  target_owner=1 if v.uid<100 else 2,target_type=target_type,
                  target_flag=y['flag'],action_type=x['action'],stance=x['stance'],last_action=x['last'],
                  current_order=x['order'],weapon_range=x['range'],state_distance=r.uniform(0,20),
                  on_patrol=x['on'],has_patrol=x['patrol'],highest_path_distance=r.uniform(0,20),
                  patrol_path_distance=r.uniform(0,20))
        c=Conversion(attacker_class=x['cls'],padawan=x['padawan'],force=x['force'],
                     target_owner=s.target_owner,target_class=s.target_class,target_id=s.target_id,
                     target_type=s.target_type,unconvertible=y['flag'],master=x['master'],
                     resource67=x['r67'],resource27=x['r27'],resource87=x['r87'])
        if kind==-1:
            allowed=False
        elif kind in (0,1):
            allowed=self.attack.base(s.attacker_class,s.attacker_id,s.target_class,s.target_id,
                                     s.invisible,s.resource31,s.owner_id,building=kind==1)
        elif kind==2:
            allowed=self.attack.tower(s.attacker_class,s.attacker_id,s.target_class,s.target_id,
                                      s.invisible,s.resource31,s.target_present,s.owner_id,s.target_owner,
                                      s.target_type,s.target_flag,x['ownState'])
        elif kind in (3,4,5):
            allowed=self.attack.soldier(s,priest=kind==4,held_attribute=x['held'],siege=kind==5,own_state=x['ownState'])
        else:
            allowed=self.attack.nullable(s.attacker_class,s.attacker_id,s.target_class,s.target_id,
                                         s.invisible,s.resource31,s.target_present,
                                         kind={6:'civilian',7:'lion',8:'medic'}[kind])
        convert=self.convert.conversion(c) if kind==4 else bool(self.attack.call(0x408B00,(v.uid,0)))
        self.counts[str(kind)]+=1
        key=str(kind)+':'+str(int(allowed))+':'+str(int(convert))
        self.outcomes[key]=self.outcomes.get(key,0)+1
        header=[kind,x['ownState'],x['held']]
        if self.source_types:header.append(x['volley'])
        return allowed,convert,[*header,*field_values(s),*field_values(c)]
