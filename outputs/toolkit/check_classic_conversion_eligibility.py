"""Compare all original conversion gates with actual x86 and compiled XS."""
from dataclasses import fields,replace
from pathlib import Path
import hashlib
import itertools
import json
import re
import struct
import subprocess
from classic_conversion_eligibility import Conversion,can_convert,EXCLUDED_IDS
from classic_conversion_eligibility_oracle import ConversionEligibilityOracle
from classic_engine_oracle import SOURCE_SHA
from check_classic_air_planner import CMAKE,PREFIX
from check_classic_soldier_eligibility import neighbors

ROOT=Path('work/classic-engine')
TOOLKIT=Path('outputs/toolkit')


def fixtures():
    values=(-1.0,-0.0,1e-45,1.0,float('nan'))
    for cls,master,r27,r87 in itertools.product((*range(-1,71),-32768,32767),(False,True),values,values):
        yield Conversion(target_class=cls,master=master,resource27=r27,resource87=r87)
    for uid,cls,kind,flag in itertools.product(sorted({n for uid in EXCLUDED_IDS for n in (uid-1,uid,uid+1)}),
                                             (7,8,32,50,64),(60,70,80,90),(0,1,255)):
        yield Conversion(target_id=uid,target_class=cls,target_type=kind,unconvertible=flag)
    for ac,padawan,force,ignore,exists,owner,r67 in itertools.product((50,51,64),(False,True),
            (-1.0,0.0,*neighbors(100.0),200.0,float('nan')),(False,True),(False,True),(0,1,2),values):
        yield Conversion(attacker_class=ac,padawan=padawan,force=force,ignore_force=ignore,
                         target_exists=exists,target_owner=owner,resource67=r67)
    # Each permission/result must refresh between calls; alternate blocked and
    # eligible identities/research rather than allocating state per fixture.
    for cls in (7,32,50,64):
        for i in range(20):
            yield Conversion(target_class=cls,master=i%2==0,resource67=float(i%3!=0))


def main():
    name='classic_conversion_eligibility.xs'
    xs=(TOOLKIT/name).read_text()
    host=ROOT/'conversion-eligibility-host';host.mkdir(parents=True,exist_ok=True)
    (host/'combined.xs').write_text(xs)
    lint=subprocess.run(['work/xs-check/xs-check.exe',str(host/'combined.xs')],capture_output=True,text=True)
    clean=re.sub(r'\x1b\[[0-9;]*m','',lint.stdout+lint.stderr)
    assert lint.returncode==0 and 'No errors found' in clean and not re.search(r'\b(?:Error|Warning):',clean),clean
    members=list(fields(Conversion))
    declarations='\n'.join(('uint32_t' if f.type is float else 'int')+' '+f.name+';' for f in members)
    reads='>>'.join(f.name for f in members)
    arguments=[('asfloat('+f.name+')' if f.type is float else f.name) for f in members]
    call=','.join(arguments[:10]);permissions=','.join(arguments[10:])
    main='#include <cstring>\n#include <cstdint>\nfloat asfloat(uint32_t b){float f;std::memcpy(&f,&b,4);return f;}\n'
    main+='int main(){'+declarations+'\nwhile(std::cin>>'+reads+') {classicConvertSetPermissions('+permissions+');'
    main+='std::cout<<classicCanConvert('+call+")<<'\\n';}\n"
    main+='if(!arrays.empty())throw std::runtime_error("Unexpected allocation");}\n'
    (host/'conversion.cpp').write_text(PREFIX+xs+main)
    (host/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(conversion LANGUAGES CXX)\nadd_executable(conversion conversion.cpp)\ntarget_compile_features(conversion PRIVATE cxx_std_17)\ntarget_compile_options(conversion PRIVATE /fp:strict)\n')
    for args in ([CMAKE,'-S',str(host),'-B',str(host/'build')],[CMAKE,'--build',str(host/'build'),'--config','Release']):
        result=subprocess.run(args,capture_output=True,text=True)
        assert result.returncode==0,result.stdout+result.stderr
    inputs,expected=[],[]
    oracle=ConversionEligibilityOracle()
    for i,s in enumerate(fixtures()):
        result=oracle.conversion(s)
        reference=can_convert(s)
        assert result==reference,(i,s,result,reference)
        row=[]
        for f in members:
            value=getattr(s,f.name)
            row.append(str(struct.unpack('<I',struct.pack('<f',value))[0] if f.type is float else int(value)))
        inputs.append(' '.join(row));expected.append(str(int(result)))
    result=subprocess.run([str(host/'build/Release/conversion.exe')],input='\n'.join(inputs)+'\n',capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    actual=result.stdout.splitlines();assert len(actual)==len(expected),(len(actual),len(expected))
    failures=[dict(case=i,input=inputs[i],actual=a,expected=b) for i,(a,b) in enumerate(zip(actual,expected)) if a!=b]
    (host/'failures.json').write_text(json.dumps(failures,indent=2)+'\n')
    assert not failures,(len(failures),failures[:3])
    names=(name,'classic_conversion_eligibility.py','classic_conversion_eligibility_oracle.py',
           'check_classic_conversion_eligibility.py','classic_engine_oracle.py',
           'check_classic_air_planner.py','check_classic_soldier_eligibility.py')
    report=dict(passed=True,cases=len(inputs),source_sha256=SOURCE_SHA,routines=['0x5B48E0'],
                tool_hashes={n:hashlib.sha256((TOOLKIT/n).read_bytes()).hexdigest() for n in names},
                installed=False,full_behavior_parity=False,
                limitations=['Padawan/Master virtual traits and world lookup are fixtures.',
                             'Caller supplies Force charge, source IDs/classes, research resources and target flags.',
                             'Eligibility only, not conversion chance/timing, order delivery or native DE XS.'])
    (ROOT/'conversion-eligibility-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',len(inputs),'conversion predicate source/XS cases; not installed')


if __name__=='__main__':main()
