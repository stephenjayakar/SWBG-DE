"""Source tactical-group list and membership mutations for the controller.

This covers container state, not targeting, path memory or order scheduling.
The next ID is supplied by the caller, as it is serialized source AI state.
"""
from dataclasses import dataclass, field, asdict


@dataclass
class Group:
    id: int = -1
    kind: int = -1
    members: list = field(default_factory=list)
    desired: int = 0
    action: int = 0
    target: int = -1
    target_type: int = -1
    in_use: int = 0
    flags: int = 32
    retreat: int = -1
    last_added: int = 0


class GroupState:
    def __init__(self, next_id=1):
        self.next_id = next_id
        self.count = 0
        self.groups = {}
        self.serial = 0

    def create(self, initialize=1, fail=False):
        if fail:
            return 0
        self.serial += 1
        group = Group()
        if initialize == 1:
            group.id = self.next_id
            self.next_id += 1
            self.count += 1
        self.groups[self.serial] = group
        return self.serial

    def add(self, handle, uid, now):
        group = self.groups[handle]
        if len(group.members) >= 40:
            return 0
        group.members.append(uid)
        group.last_added = now
        return 1

    def remove(self, handle, uid):
        group = self.groups[handle]
        if uid not in group.members:
            return 0
        group.members.remove(uid)
        return 1

    def delete(self, gid):
        for handle, group in self.groups.items():
            if group.id == gid:
                del self.groups[handle]
                self.count -= 1
                return 1
        return 0

    def delete_kind(self, kind):
        for handle, group in list(self.groups.items()):
            if kind == -1 or group.kind == kind:
                del self.groups[handle]
                self.count -= 1
        return 1

    def containing(self, uid):
        return next((handle for handle, group in self.groups.items() if uid in group.members), 0)

    def snapshot(self):
        return dict(next_id=self.next_id, count=self.count,
                    groups=[asdict(group) for group in self.groups.values()])
