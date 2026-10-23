"""Original GetVisibleUnits ordered distance/radius filtering and bucket caps."""
import math

def build_table(spans):
    table=[255]*1024
    for distance,rows in enumerate(spans):
        for y,lo,hi in rows:
            if 0<=y<=31:
                for x in range(max(0,lo),min(31,hi)+1):
                    if table[y*32+x]==255:table[y*32+x]=distance
    for y in range(32):
        for x in range(32):
            if table[y*32+x]==255:table[y*32+x]=int(math.sqrt(x*x+y*y)+0.5)
    return bytes(table)

def scan(table,categories,desired,relations,x,y,los,player=1,players=3,prior=None):
    previous=prior if prior is not None else [[] for _ in range(5)]
    if not desired or player>=players:return 0,[list(g) for g in previous]
    groups=[[] for _ in range(5)];los=min(15,los)
    for category in desired:
        for uid,radius,owner,rx,ry in categories[category]:
            if rx<x-los-7 or rx>x+los+7 or ry<y-los-7 or ry>y+los+7:continue
            distance=table[(abs(ry-y)&31)*32+(abs(rx-x)&31)]
            if distance>los:
                distance-=radius
                if distance<=0:distance=1
                elif distance>los:continue
            group=groups[relations[owner]]
            if len(group)<256:group.append((uid,distance,owner,rx,ry))
    return sum(map(len,groups)),groups

def generate_table(table):
    text='// Generated from source Build_Distance_Table; original construction checked.\nint classicVisibleDistanceTable = -1;\n'
    # Split initializers to keep bytecode/function size bounded.
    for block in range(8):
        text+=f'void classicVisibleDistanceInit{block}() {{\n'
        for index in range(block*128,(block+1)*128):
            text+=f'    xsArraySetInt(classicVisibleDistanceTable, {index}, {table[index]});\n'
        text+='}\n'
    text+='void classicVisibleDistanceInit() {\n    if (classicVisibleDistanceTable >= 0) return;\n'
    text+='    classicVisibleDistanceTable = xsArrayCreateInt(1024, 0, "source visible distances");\n'
    text+=''.join(f'    classicVisibleDistanceInit{block}();\n' for block in range(8))+'}\n'
    return text
