"""Compare source event wrappers, reference records and composed XS scans."""
from pathlib import Path
from collections import Counter
import json,random,re,subprocess
from classic_visible_records import VisibleRecords,trunc
from classic_visible_records_oracle import VisibleRecordsOracle,bits,f32
from classic_visible_scan_oracle import VisibleScanOracle
from classic_visible_scan import scan,generate_table
from classic_unit_identity import sha
from classic_engine_oracle import SOURCE_SHA
from check_classic_air_planner import CMAKE,PREFIX
from check_classic_attack_dispatch_xs import EXTRA

ROOT=Path('work/classic-engine/visible-records-host');TOOLKIT=Path('outputs/toolkit')
MAIN=r'''
#include <cstring>
#include <cstdint>
float frombits(uint32_t b){float f;std::memcpy(&f,&b,4);return f;}
void records(){
    for(int p=0;p<classicVMemberPlayers;p++)for(int c=0;c<classicVMemberCategories;c++){
        int list=p*classicVMemberCategories+c,base=xsArrayGetInt(classicVMemberBases,list),n=xsArrayGetInt(classicVMemberCounts,list);
        std::cout<<xsArrayGetInt(classicVMemberCaps,list)<<' '<<n<<' ';
        for(int i=0;i<n;i++){int at=base+i,uid=xsArrayGetInt(classicVMemberIDs,at),d=xsArrayGetInt(classicVMemberDetails,at),pos=xsArrayGetInt(classicVMemberPositions,at);
            std::cout<<uid<<' '<<d%256<<' '<<d/256<<' '<<pos%256<<' '<<pos/256<<' ';
            if(xsArrayGetInt(classicVMemberPointers,uid*classicVMemberPlayers+p)!=at)throw std::runtime_error("Unrepaired pointer");
        }
    }
}
int main(){char mode;int desired=xsArrayCreateInt(20,0,"desired"),relations=xsArrayCreateInt(256,0,"relations");
while(std::cin>>mode){
    int uid,owner,radius,cat,oldMask,newMask;
    if(mode=='R'){int players,categories;std::cin>>players>>categories;classicVisibilityReset(players,categories);continue;}
    if(mode=='U'){int x,y;std::cin>>uid>>owner>>x>>y>>radius>>cat>>oldMask>>newMask;
        classicVMemberSetLookup(uid,true);
        if(!classicVMemberUpdate(uid,owner,x,y,radius,cat,oldMask,newMask))throw std::runtime_error("Bad event");}
    else if(mode=='M'){uint32_t ox,oy,nx,ny;std::cin>>uid>>ox>>oy>>nx>>ny;
        classicVRecordMove(uid,frombits(ox),frombits(oy),frombits(nx),frombits(ny));}
    else if(mode=='O'){std::cin>>uid>>owner;classicVRecordOwner(uid,owner);}
    else if(mode=='T'){uint32_t x,y;int oldCat;std::cin>>uid>>oldCat>>oldMask>>owner>>x>>y>>radius>>cat>>newMask;
        if(!classicVRecordTransformBefore(uid,oldCat,oldMask))throw std::runtime_error("Bad removal");
        records();std::cout<<'\n';
        if(!classicVRecordTransformAfter(uid,owner,frombits(x),frombits(y),radius,cat,newMask))throw std::runtime_error("Bad insertion");}
    else throw std::runtime_error("Unknown mode");
    records();
    int qx,qy,los,player,nd;std::cin>>qx>>qy>>los>>player>>nd;
    for(int i=0;i<nd;i++){int v;std::cin>>v;xsArraySetInt(desired,i,v);}
    for(int i=0;i<256;i++){int v;std::cin>>v;xsArraySetInt(relations,i,v);}
    std::cout<<classicVisibilityScan(qx,qy,los,player,desired,nd,relations);
    for(int g=0;g<5;g++){int n=xsArrayGetInt(classicVisibleCounts,g);std::cout<<' '<<n;
        for(int i=0;i<n;i++){int at=g*256+i,d=xsArrayGetInt(classicVisibleDetails,at),p=xsArrayGetInt(classicVisiblePositions,at);
            std::cout<<' '<<xsArrayGetInt(classicVisibleIDs,at)<<' '<<d%256<<' '<<d/256<<' '<<p%256<<' '<<p/256;}}
    std::cout<<'\n';if(arrays.size()!=15)throw std::runtime_error("Leaked arrays");
}}
'''

def flattened(snapshot):
    rows,caps,_=snapshot;out=[]
    for player,categories in enumerate(rows):
        for cat,bucket in enumerate(categories):
            out.extend((caps[player][cat],len(bucket)))
            out.extend(v for record in bucket for v in record)
    return out

def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    table,_=VisibleScanOracle().distance_table();generated=generate_table(table)
    names=('classic_visible_membership.xs','classic_visible_records.xs','classic_visible_scan.xs','classic_visible_pipeline.xs')
    xs=generated+'\n'+'\n'.join((TOOLKIT/n).read_text() for n in names)
    (ROOT/'combined.xs').write_text(xs)
    lint=subprocess.run(['work/xs-check/xs-check.exe',str(ROOT/'combined.xs')],capture_output=True,text=True)
    clean=re.sub(r'\x1b\[[0-9;]*m','',lint.stdout+lint.stderr)
    assert lint.returncode==0 and 'No errors found' in clean and not re.search(r'\b(?:Error|Warning):',clean),clean
    cpp=re.sub(r'for \((\w+) = ([^;]+); < ([^)]+)\)',lambda m:f'for (int {m[1]} = {m[2]}; {m[1]} < {m[3]}; {m[1]}++)',xs)
    (ROOT/'records.cpp').write_text(PREFIX+EXTRA+cpp+MAIN)
    (ROOT/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(records LANGUAGES CXX)\nadd_executable(records records.cpp)\ntarget_compile_features(records PRIVATE cxx_std_17)\ntarget_compile_options(records PRIVATE /fp:strict)\n')
    for args in ([CMAKE,'-S',str(ROOT),'-B',str(ROOT/'build')],[CMAKE,'--build',str(ROOT/'build'),'--config','Release']):
        run=subprocess.run(args,capture_output=True,text=True);assert run.returncode==0,run.stdout+run.stderr

    rng=random.Random(4461);oracle=VisibleRecordsOracle();inputs=[];expected=[];counts=Counter();traces=[]
    for players in (0,1,3,9):
        categories=2;full=(1<<players)-1;model=VisibleRecords(players,categories)
        oracle.initialize(players,categories);oracle.cpu.mem_write(oracle.obj(-1),bytes(0x200))
        inputs.append(f'R {players} {categories}');prior=[[] for _ in range(5)];states={};trace=[]

        def event(mode,args):
            nonlocal prior
            counts[mode]+=1;uid=args[0];step=len(trace);line=[mode,*args]
            if mode=='U':
                oracle.update(*args);model.update(*args)
            elif mode=='M':
                oracle.move(*args);model.move(*args);line=[mode,uid,*map(bits,args[1:])]
                if (trunc(args[1]),trunc(args[2]))==(trunc(args[3]),trunc(args[4])):counts['same_tile_moves']+=1
            elif mode=='O':oracle.owner_prefix(*args);model.owner(*args)
            elif mode=='T':
                old,new=args[1:];middle=oracle.transform(uid,old,new)
                model.before(uid,old[4],old[5]);assert middle==model.snapshot()
                expected.append(' '.join(map(str,flattened(middle))))
                model.after(uid,*new)
                line=[mode,uid,old[4],old[5],new[0],bits(new[1]),bits(new[2]),new[3],new[4],new[5]]
                if old[4]==new[4]:counts['same_category_transforms']+=1
            snapshot=oracle.snapshot();assert snapshot==model.snapshot(),(players,step,mode)
            inputs.append(' '.join(map(str,line)))
            query_player=step%(players+1);desired=[] if step%19==0 else [step%3,0,1,2,0]
            relations=[(i+step)%5 for i in range(256)]
            qx,qy=(step%30,step%25) if step%2 else (128,128)
            los=(0,5,15,50)[step%4];query=[qx,qy,los,query_player,len(desired),*desired,*relations]
            inputs.append(' '.join(map(str,query)))
            actual=oracle.scan(qx,qy,los,query_player,desired,relations)
            rows=model.rows[query_player] if query_player<players else [[],[],[]]
            reference=scan(table,rows,desired,relations,qx,qy,los,query_player,players,prior)
            assert actual==reference,(players,step,actual,reference)
            total,prior=actual;out=flattened(snapshot)+[total]
            counts['returned_records']+=total
            if not desired or query_player>=players:counts['retained_buffers']+=1
            for bucket in prior:out.append(len(bucket));out.extend(v for record in bucket for v in record)
            expected.append(' '.join(map(str,out)));trace.append(dict(mode=mode,args=args,query=query))

        # Force growth, mixed null/non-null pointers, then move/remove/reinsert
        # through repaired references. Source supports exactly nine pointer slots.
        for uid in range(150):
            state=(uid%3,float(uid%20),float(uid%25),uid%8,0 if uid<90 else 1,full)
            states[uid]=state
            event('U',(uid,state[0],trunc(state[1]),trunc(state[2]),*state[3:5],0,state[5]))
        for step in range(520):
            uid=rng.randrange(150);old=states[uid];mode=('M','O','T','U')[step%4]
            if mode=='M':
                # Include unchanged tiles, zero crossings, negatives and byte wraps.
                if step%12==0:nx,ny=trunc(old[1])+.125,trunc(old[2])+.25
                else:nx,ny=rng.choice((-256.75,-1.75,-.75,.75,1.75,20.5,255.5,256.5,512.25)),rng.uniform(-2,28)
                nx,ny=f32(nx),f32(ny);event(mode,(uid,old[1],old[2],nx,ny))
                states[uid]=(old[0],nx,ny,*old[3:])
            elif mode=='O':
                owner=rng.choice((-257,-1,0,1,2,255,256,257,65535))
                event(mode,(uid,owner));states[uid]=(owner,*old[1:])
            elif mode=='T':
                new=(rng.randrange(3),f32(rng.uniform(0,30)),f32(rng.uniform(0,30)),rng.randrange(256),rng.randrange(3),rng.randrange(full+1))
                event(mode,(uid,old,new));states[uid]=new
            else:
                mask=rng.randrange(full+1)
                event(mode,(uid,old[0],trunc(old[1]),trunc(old[2]),old[3],old[4],old[5],mask))
                states[uid]=(*old[:5],mask)
        # Challenge the negative-ID guard with live record pointers on a fixture
        # object. The source must skip writes even when those pointers are nonnull.
        oracle.cpu.mem_write(oracle.obj(-1)+0x144,bytes(oracle.cpu.mem_read(oracle.obj(0)+0x144,36)))
        event('M',(-1,0.0,0.0,25.0,25.0));event('O',(-1,255))
        traces.append(dict(players=players,categories=categories,events=trace))
        counts['growths']+=model.growths
    run=subprocess.run([str(ROOT/'build/Release/records.exe')],input='\n'.join(inputs)+'\n',capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    actual=[line.strip() for line in run.stdout.splitlines()];assert len(actual)==len(expected),(len(actual),len(expected))
    for i,(a,b) in enumerate(zip(actual,expected)):assert a==b,(i,a[:200],b[:200])
    trace_path=ROOT.parent/'visible-records-traces.json';trace_path.write_text(json.dumps(traces)+'\n')
    hashes={n:sha(TOOLKIT/n) for n in (*names,'classic_visible_records.py','classic_visible_records_oracle.py','classic_visible_membership.py','classic_visible_membership_oracle.py','classic_visible_scan.py','classic_visible_scan_oracle.py','check_classic_visible_records.py')}
    report=dict(passed=True,counts=dict(counts),compared_states=len(expected),source_sha256=SOURCE_SHA,
        hashes=hashes,trace_sha256=sha(trace_path),installed=False,engine_verified=False,full_behavior_parity=False,
        limitations=['Movement base call supplies resolved coordinates; source movement/collision/pathfinding is not executed.',
                     'Ownership executes only the record-update prefix, not complete conversion.',
                     'Transformation executes original remove/base/add wrapper with supplied base mutations.',
                     'Source visibility events, lookup and diplomacy are fixtures; native lifecycle/scheduling is not connected.',
                     'Original returned scan buffers remain snapshots until a query replaces them.'])
    (ROOT.parent/'visible-records-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS {len(expected)} source/reference/XS states; {dict(counts)}')

if __name__=='__main__':main()
