// Original gbg_isPadawan (0x54B170) / gbg_isMaster (0x54B1D0).
// Master id (+0x18) and copy_id (+0x1A) are intentionally separate.
bool classicForcePadawan(int sourceID = -1, int copyID = -1) {
    return(copyID == 180 || copyID == 183 || copyID == 232 || copyID == 204 ||
           copyID == 52 || copyID == 239 || copyID == 647 || copyID == 652 ||
           sourceID == 1075 || sourceID == 1076 || sourceID == 800 ||
           sourceID == 814 || sourceID == 824);
}
bool classicForceMaster(int sourceID = -1, int copyID = -1) {
    return(copyID == 115 || copyID == 125 || copyID == 136 || copyID == 134 ||
           copyID == 89 || copyID == 140 || copyID == 643 || copyID == 645 ||
           sourceID == 1077 || sourceID == 1085 || sourceID == 1082 || sourceID == 1084 ||
           sourceID == 1080 || sourceID == 725 || sourceID == 728 || sourceID == 731 ||
           sourceID == 747 || sourceID == 753 || sourceID == 761 || sourceID == 770 ||
           sourceID == 778 || sourceID == 784 || sourceID == 806 || sourceID == 792);
}

bool classicForceRankReady = false;
bool classicForceObservedPadawan = false;
bool classicForceObservedMaster = false;
int classicForceObservedOwner = -1;
int classicForceObservedSourceID = -1;
int classicForceObservedCopyID = -1;
float classicForceObservedAirResearch = 0.0;

// Native getter contract remains to be checked across DE upgrades. Use the
// raw/object ID for the raw branch, and the upgraded copy ID for the copy branch.
bool classicForceObserveRank(int unit = -1) {
    classicForceRankReady = false;
    classicForceObservedPadawan = false;
    classicForceObservedMaster = false;
    classicForceObservedOwner = -1;
    classicForceObservedSourceID = -1;
    classicForceObservedCopyID = -1;
    classicForceObservedAirResearch = 0.0;
    classicConvertSetPermissions(false, 0.0, 0.0, 0.0);
    if (xsDoesUnitExist(unit) == false) return(false);
    int owner = xsGetUnitOwner(unit);
    int civ = 0;
    if (owner != 0) civ = xsGetPlayerCivilization(owner);
    int raw = xsGetUnitObjectId(unit);
    int copy = xsGetUnitCopyId(unit);
    if (classicSourcePacked(raw,civ) < 0 || classicSourcePacked(copy,civ) < 0) return(false);
    classicForceObservedPadawan = classicForcePadawan(raw,copy);
    classicForceObservedMaster = classicForceMaster(raw,copy);
    classicForceObservedOwner = owner;
    classicForceObservedSourceID = raw;
    classicForceObservedCopyID = copy;
    classicForceRankReady = true;
    return(true);
}

// Current resource mapping: source 27/67 retain native slots; source 31/87
// are stored in custom slots 2031/2087. This observes research permission,
// not the adapted native conversion ability's charge/timing/chance.
bool classicForceObservePermissions(int unit = -1) {
    if (classicForceObserveRank(unit) == false) return(false);
    int owner = classicForceObservedOwner;
    classicForceObservedAirResearch = xsPlayerAttribute(owner,2031);
    classicConvertSetPermissions(classicForceObservedMaster, xsPlayerAttribute(owner,67),
        xsPlayerAttribute(owner,27), xsPlayerAttribute(owner,2087));
    return(true);
}
