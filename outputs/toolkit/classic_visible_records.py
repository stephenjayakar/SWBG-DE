"""Reference visibility-record effects, on supplied source event boundaries."""
import struct
from classic_visible_membership import VisibleMembership

def trunc(value):return int(struct.unpack('<f',struct.pack('<f',value))[0])

class VisibleRecords(VisibleMembership):
    def move(self,uid,old_x,old_y,new_x,new_y):
        if uid<0:return
        x,y=trunc(new_x),trunc(new_y)
        if (trunc(old_x),trunc(old_y))==(x,y):return
        for player in range(self.players):
            ref=self.pointers.get((uid,player))
            if ref is not None:
                category,index=ref;record=self.rows[player][category][index]
                self.rows[player][category][index]=(*record[:3],x&255,y&255)

    def owner(self,uid,owner):
        if uid<0:return
        for player in range(self.players):
            ref=self.pointers.get((uid,player))
            if ref is not None:
                category,index=ref;record=self.rows[player][category][index]
                self.rows[player][category][index]=(record[0],record[1],owner&255,*record[3:])

    def before(self,uid,category,mask):
        if uid>=0:self.update(uid,0,0,0,0,category,mask,0)

    def after(self,uid,owner,x,y,radius,category,mask):
        if uid>=0:self.update(uid,owner,trunc(x),trunc(y),radius,category,0,mask)
