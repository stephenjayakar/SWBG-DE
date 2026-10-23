// Visibility-record side effects of movement, ownership and transformation.
// Requires classic_visible_membership.xs. Inputs are source-equivalent events,
// not native observations. Coordinates must be finite and fit signed int32.
int classicVRecordTrunc(float value = 0.0) {
    int result = xsCeilToInt(value);
    if (value > 0.0 && result > value) result = result-1;
    return(result);
}

// RGE_Combat_Object::teleport (0x4461E0) reads the position AFTER its base
// movement call. Pass that resolved position, not the requested destination.
void classicVRecordMove(int unit = -1, float oldX = 0.0, float oldY = 0.0,
    float newX = 0.0, float newY = 0.0) {
    if (unit < 0) return;
    int x = classicVRecordTrunc(newX);
    int y = classicVRecordTrunc(newY);
    if (x == classicVRecordTrunc(oldX) && y == classicVRecordTrunc(oldY)) return;
    classicVMemberEnsureUnit(unit);
    int position = (x%256+256)%256+((y%256+256)%256)*256;
    for (player = 0; < classicVMemberPlayers) {
        int at = xsArrayGetInt(classicVMemberPointers, unit*classicVMemberPlayers+player);
        if (at >= 0) xsArraySetInt(classicVMemberPositions, at, position);
    }
}

// Prefix of TRIBE_Combat_Object::change_ownership (0x55B820). The owner byte
// changes before the rest of conversion/ownership processing. No list reorder.
void classicVRecordOwner(int unit = -1, int owner = 0) {
    if (unit < 0) return;
    classicVMemberEnsureUnit(unit);
    int byteOwner = (owner%256+256)%256;
    for (player = 0; < classicVMemberPlayers) {
        int at = xsArrayGetInt(classicVMemberPointers, unit*classicVMemberPlayers+player);
        if (at >= 0) {
            int radius = xsArrayGetInt(classicVMemberDetails, at)%256;
            xsArraySetInt(classicVMemberDetails, at, radius+byteOwner*256);
        }
    }
}

// RGE_Combat_Object::transform (0x443E20) removes visible records before the
// base transformation and appends replacements afterward, even in one category.
// Invoke the two phases around the caller's base transformation boundary.
bool classicVRecordTransformBefore(int unit = -1, int category = 0, int mask = 0) {
    if (unit < 0) return(true);
    // Position/owner/radius are ignored by source removal; pointers identify rows.
    return(classicVMemberUpdate(unit, 0, 0, 0, 0, category, mask, 0));
}
bool classicVRecordTransformAfter(int unit = -1, int owner = 0,
    float x = 0.0, float y = 0.0, int radius = 0, int category = 0, int mask = 0) {
    if (unit < 0) return(true);
    return(classicVMemberUpdate(unit, owner, classicVRecordTrunc(x), classicVRecordTrunc(y),
        radius, category, 0, mask));
}
