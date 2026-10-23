"""Lossless SMX damage-mask adapter, preserving every other encoded field.

Reference: https://github.com/SFTtech/openage/blob/master/doc/media/smx-files.md
The 4+1 representation omits damage modifiers; 8-to-5 stores two 10-bit palette
indices and damage values. Command streams, shadows and outlines are untouched.
"""
import struct
import numpy as np

def neutralize(data):
    assert data[:4]==b'SMPX' and len(data)>=32
    count=struct.unpack_from('<H',data,6)[0];pos=32;out=bytearray(data[:32])
    stats=dict(frames=count,visible_frames=0,missing_frames=0,nonneutral_frames=0,pixels=0)
    for _ in range(count):
        frame=bytearray(data[pos:pos+6]);pos+=6;flags=frame[0];parts=[]
        assert not flags&0xe0,('Unknown SMX flags',flags)
        for layer in (1,2,4):
            if not flags&layer:continue
            start=pos;w,h,ax,ay,size,unknown=struct.unpack_from('<HHhhII',data,pos)
            end=pos+16+size;assert end<=len(data)
            if layer!=1:
                parts.append(data[start:end]);pos=end;continue
            lengths=pos+16+4*h
            ncmd,npix=struct.unpack_from('<II',data,lengths)
            cmdstart=lengths+8;pixstart=cmdstart+ncmd
            assert pixstart+npix==end
            commands=np.frombuffer(data[cmdstart:pixstart],dtype=np.uint8)
            types=commands&3
            pixels=int(((commands[(types==1)|(types==2)].astype(np.uint32)>>2)+1).sum())
            if pixels==0:
                parts.append(data[start:end]);pos=end;continue
            stats['visible_frames']+=1;stats['pixels']+=pixels
            packed=np.frombuffer(data[pixstart:end],dtype=np.uint8).reshape(-1,5)
            if flags&8:
                assert len(packed)==(pixels+1)//2
                bad=bool(np.any(packed[:,2]&0xf0) or np.any(packed[:,3:]))
                stats['nonneutral_frames']+=int(bad)
                fixed=packed.copy();fixed[:,2]&=0x0f;fixed[:,3:]=0
            else:
                stats['missing_frames']+=1
                assert len(packed)==(pixels+3)//4
                indices=packed[:,:4].astype(np.uint16)
                for i in range(4):indices[:,i]|=((packed[:,4].astype(np.uint16)>>(i*2))&3)<<8
                indices=indices.reshape(-1)[:pixels]
                pairs=np.zeros(((pixels+1)//2,2),dtype=np.uint16);pairs.reshape(-1)[:pixels]=indices
                fixed=np.zeros((len(pairs),5),dtype=np.uint8)
                fixed[:,0]=pairs[:,0]&255
                fixed[:,1]=((pairs[:,0]>>8)&3)|((pairs[:,1]&63)<<2)
                fixed[:,2]=(pairs[:,1]>>6)&15
            encoded=fixed.tobytes();frame[0]|=8
            new=bytearray(data[start:pixstart]);struct.pack_into('<I',new,8,size+len(encoded)-npix)
            struct.pack_into('<I',new,lengths-start+4,len(encoded));new.extend(encoded)
            parts.append(new);pos=end
        out.extend(frame)
        for part in parts:out.extend(part)
    assert pos==len(data),('Trailing SMX data',pos,len(data))
    struct.pack_into('<I',out,8,len(out)-32)
    return bytes(out),stats
