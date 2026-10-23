"""Original priest bestUnitToConvert (0x5B4E80), ordered supplied candidates."""
from dataclasses import dataclass
import struct

def f32(v):return struct.unpack('<f',struct.pack('<f',v))[0]

@dataclass(frozen=True)
class Candidate:
    uid:int=1
    enemy:bool=True
    present:bool=True
    state:int=2
    convertible:bool=True
    distance:int=1
    max_hp:int=100
    source_class:int=32
    memory_owner:int=2

def select(candidates,initial_distance=-123.):
    chosen=-1;best=f32(0);distance=f32(initial_distance)
    for c in candidates:
        if not c.enemy or not c.present or (c.state&255)>=3 or not c.convertible:continue
        dist=max(1,c.distance&255)
        hp=(c.max_hp+32768)%65536-32768
        cls=(c.source_class+32768)%65536-32768
        value=hp/(dist+4 if cls==47 else dist)
        # Source compares the extended ratio against a stored float32 score.
        # Identical repeated ratios can replace one another when rounded down.
        if chosen==-1 or value>best:
            chosen=c.uid;best=f32(value);distance=f32(dist)
    return chosen,distance,best
