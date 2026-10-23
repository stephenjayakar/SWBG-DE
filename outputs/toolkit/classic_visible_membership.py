"""Original visible category-list membership ordering; source event inputs required."""
class VisibleMembership:
    def __init__(self,players,categories):
        self.players=players;self.categories=categories+1
        self.rows=[[[] for _ in range(self.categories)] for _ in range(players)]
        self.capacity=[[64]*self.categories for _ in range(players)]
        self.pointers={}
        self.growths=0

    def update(self,uid,owner,x,y,radius,category,prior,new):
        assert category>=0
        if category>=self.categories:return
        delta=(prior^new)&65535
        for player in range(self.players):
            if not delta:break
            if delta&1:
                bucket=self.rows[player][category]
                if new&1:
                    if len(bucket)==self.capacity[player][category]:
                        self.capacity[player][category]*=2;self.growths+=1
                    self.pointers[uid,player]=(category,len(bucket))
                    bucket.append((uid,radius&255,owner&255,x&255,y&255))
                else:
                    # Source requires a valid record pointer for a removed bit.
                    old_category,index=self.pointers[uid,player]
                    assert old_category==category and index<len(bucket)
                    last=bucket[-1]
                    if index!=len(bucket)-1:
                        bucket[index]=last;self.pointers[last[0],player]=(category,index)
                    bucket.pop();self.pointers[uid,player]=None
            new>>=1;delta>>=1

    def snapshot(self):
        return self.rows,self.capacity,{key:value for key,value in self.pointers.items() if value is not None}
