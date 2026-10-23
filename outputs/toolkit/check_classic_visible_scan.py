"""Compare source distance construction and ordered visible-result buckets."""
from pathlib import Path
import hashlib,itertools,json,random,re,subprocess
from classic_visible_scan import build_table,scan,generate_table
from classic_visible_scan_oracle import VisibleScanOracle
from classic_unit_identity import sha
from check_classic_air_planner import CMAKE,PREFIX

ROOT=Path('work/classic-engine/visible-scan-host');TOOLKIT=Path('outputs/toolkit')
MAIN=r'''
int main(){int x,y,los,player,players,nd,n;
while(std::cin>>x>>y>>los>>player>>players>>nd>>n){
    classicVisibleInit();
    for(int g=0;g<5;g++){int count;std::cin>>count;xsArraySetInt(classicVisibleCounts,g,count);
        for(int i=0;i<count;i++){int id,d,o,px,py;std::cin>>id>>d>>o>>px>>py;int at=g*256+i;
            xsArraySetInt(classicVisibleIDs,at,id);xsArraySetInt(classicVisibleDetails,at,d+o*256);
            xsArraySetInt(classicVisiblePositions,at,px+py*256);}}
    bool accepted=classicVisibleBegin(x,y,los,player,players,nd);
    for(int i=0;i<n;i++){int id,r,o,px,py,g;std::cin>>id>>r>>o>>px>>py>>g;classicVisibleAdd(id,r,o,px,py,g);}
    std::cout<<accepted<<' '<<classicVisibleEnd();
    for(int g=0;g<5;g++){int count=xsArrayGetInt(classicVisibleCounts,g);std::cout<<' '<<count;
        for(int i=0;i<count;i++){int at=g*256+i,d=xsArrayGetInt(classicVisibleDetails,at),p=xsArrayGetInt(classicVisiblePositions,at);
            std::cout<<' '<<xsArrayGetInt(classicVisibleIDs,at)<<' '<<d%256<<' '<<d/256<<' '<<p%256<<' '<<p/256;}}
    std::cout<<'\n';if(arrays.size()!=5)throw std::runtime_error("Scan leaked arrays");
}}
'''
def fixtures():
    relations=[i%5 for i in range(256)]
    prior=[[(901+g,3,g,10,20)] for g in range(5)]
    yield [[]],[0],relations,10,10,15,1,3,prior
    # A visible center tile keeps distance zero, while a radius-rescued record
    # gets distance one. Distances already within LOS do not subtract radius.
    for los in (0,1,5):
        yield [[(1,255,0,10,10),(2,255,1,11,10),(3,2,2,12,10)]],[0],relations,10,10,los,1,3,prior
    for x,y,los in itertools.product((0,1,31,128,254,255,256,300), (0,128,255),(-8,-1,0,1,7,15,16,40)):
        # Every byte delta around the center, including outside the bounding box.
        cats=[[(1000+i,i%8,i%256,(x+i)%256,(y+i//32)%256) for i in range(1024)]]
        yield cats,[0],relations,x,y,los,1,3,prior
    # Radius changes distance only outside LOS; category duplication and bucket caps.
    for radius,los in itertools.product((0,1,7,31,255),(-1,0,1,7,15,16)):
        cats=[[(i,radius,i%5,128+i%23,128) for i in range(1400)],[(5000+i,radius,i%5,128,128) for i in range(1400)]]
        yield cats,[1,0,1],relations,128,128,los,1,3,prior
    for desired,player,players in itertools.product(([],[0]),(0,1,3,4),(0,1,3)):
        yield [[(42,0,2,10,10)]],desired,relations,10,10,15,player,players,prior
    rng=random.Random(0x614A00)
    for i in range(120):
        cats=[[(rng.randrange(100),rng.randrange(256),rng.randrange(256),rng.randrange(256),rng.randrange(256))
               for _ in range(rng.randrange(400))] for _ in range(rng.randrange(1,6))]
        yield (cats,[rng.randrange(len(cats)) for _ in range(rng.randrange(9))],
               [rng.randrange(5) for _ in range(256)],rng.randrange(-20,280),rng.randrange(-20,280),
               rng.randrange(-8,32),rng.randrange(4),3,prior)

def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    oracle=VisibleScanOracle();table,spans=oracle.distance_table();assert table==build_table(spans)
    assert hashlib.sha256(table).hexdigest()=='666523e019b063e7204e020aba8adceec045b097770276c92bb266b61eeefd9c'
    generated=ROOT/'classic_visible_distance.xs';generated.write_text(generate_table(table))
    xs=generated.read_text()+'\n'+(TOOLKIT/'classic_visible_scan.xs').read_text()
    (ROOT/'combined.xs').write_text(xs)
    lint=subprocess.run(['work/xs-check/xs-check.exe',str(ROOT/'combined.xs')],capture_output=True,text=True)
    clean=re.sub(r'\x1b\[[0-9;]*m','',lint.stdout+lint.stderr)
    assert lint.returncode==0 and 'No errors found' in clean and not re.search(r'\b(?:Error|Warning):',clean),clean
    cpp=re.sub(r'for \((\w+) = ([^;]+); < ([^)]+)\)',lambda m:f'for (int {m[1]} = {m[2]}; {m[1]} < {m[3]}; {m[1]}++)',xs)
    (ROOT/'scan.cpp').write_text(PREFIX+cpp+MAIN)
    (ROOT/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(scan LANGUAGES CXX)\nadd_executable(scan scan.cpp)\ntarget_compile_features(scan PRIVATE cxx_std_17)\n')
    for args in ([CMAKE,'-S',str(ROOT),'-B',str(ROOT/'build')],[CMAKE,'--build',str(ROOT/'build'),'--config','Release']):
        run=subprocess.run(args,capture_output=True,text=True);assert run.returncode==0,run.stdout+run.stderr
    inputs=[];expected=[];rejections=0;full=0;records=0
    for i,args in enumerate(fixtures()):
        cats,desired,relations,x,y,los,player,players,prior=args
        result=oracle.scan(table,*args);reference=scan(table,*args);assert result==reference,(i,result,reference)
        accepted=bool(desired) and player<players;rejections+=not accepted
        total,groups=result;full+=sum(len(g)==256 for g in groups);records+=total
        flattened=[r for category in desired for r in cats[category]]
        inputs.append(' '.join(map(str,(x,y,los,player,players,len(desired),len(flattened)))))
        for group in prior:
            inputs.append(str(len(group)));inputs.extend(' '.join(map(str,r)) for r in group)
        inputs.extend(' '.join(map(str,(*r,relations[r[2]]))) for r in flattened)
        output=[int(accepted),total]
        for group in groups:
            output.append(len(group));output.extend(v for r in group for v in r)
        expected.append(' '.join(map(str,output)))
    run=subprocess.run([str(ROOT/'build/Release/scan.exe')],input='\n'.join(inputs)+'\n',capture_output=True,text=True)
    assert run.returncode==0,run.stderr
    actual=run.stdout.splitlines();assert len(actual)==len(expected)
    for i,(a,b) in enumerate(zip(actual,expected)):assert a==b,(i,a[:250],b[:250])
    report=dict(passed=True,cases=len(expected),early_returns=rejections,full_buckets=full,returned_records=records,
        distance_table_sha256=hashlib.sha256(table).hexdigest(),distance_cells=len(table),span_lists=len(spans),
        tool_hashes={n:sha(TOOLKIT/n) for n in ('classic_visible_scan.py','classic_visible_scan.xs','classic_visible_scan_oracle.py','check_classic_visible_scan.py')},
        generated_sha256=sha(generated),installed=False,full_behavior_parity=False,
        limitations=['Source category membership/order and player relation map are fixture inputs.',
                     'Native visibility lifecycle, UnitAI scan cache, notifications and command delivery remain unfinished.'])
    (ROOT.parent/'visible-scan-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS {len(expected)} source/XS scans / {rejections} early returns / {full} full buckets / {records} records')

if __name__=='__main__':main()
