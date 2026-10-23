// Development-only TribePriestUnitAIModule::canConvert (0x5B48E0).
// Supply this attacker's research/master state immediately before its query.
bool classicConvertEnabled = false;
bool classicConvertForceUsers = false;
bool classicConvertMechanical = false;
void classicConvertSetPermissions(bool master = false, float resource67 = 0.0,
                                  float resource27 = 0.0, float resource87 = 0.0) {
    classicConvertEnabled = resource67 > 0.0;
    classicConvertForceUsers = master && resource27 > 0.0;
    classicConvertMechanical = master && resource87 > 0.0;
}

bool classicCanConvert(int attackerClass = -1, bool padawan = false,
                       float force = 0.0, bool ignoreForce = false,
                       bool targetExists = false, int targetOwner = 0,
                       int targetClass = -1, int targetID = -1,
                       int targetType = 70, int unconvertible = 0) {
    if (padawan || attackerClass == 51) return (false);
    if ((force >= 100.0) == false && ignoreForce == false) return (false);
    if (targetExists == false || targetOwner == 0 || classicConvertEnabled == false) return (false);
    if (targetClass == 1 || targetClass == 2 || targetClass == 3 || targetClass == 4 ||
        targetClass == 60 || targetClass == 5 || targetClass == 44 || targetClass == 46 ||
        targetClass == 51 || targetClass == 6 || targetClass == 8 || targetClass == 26 || targetClass == 62) return (false);
    if (targetID == 4 || targetID == 977 || targetID == 109 || targetID == 276 ||
        targetID == 82 || targetID == 104 || targetID == 24 || targetID == 199 || targetID == 50) return (false);
    if ((targetType == 70 || targetType == 80) && unconvertible != 0) return (false);
    if ((targetClass == 50 || targetClass == 64) && classicConvertForceUsers == false) return (false);
    bool mechanical = targetClass == 32 || targetClass == 33 || targetClass == 34 ||
        targetClass == 35 || targetClass == 36 || targetClass == 59 || targetClass == 43 ||
        targetClass == 45 || targetClass == 48 || targetClass == 63 || targetClass == 53 ||
        targetClass == 57 || targetClass == 18 || targetClass == 9 || targetClass == 10 ||
        targetClass == 11 || targetClass == 12 || targetClass == 13 || targetClass == 14 ||
        targetClass == 15 || targetClass == 16 || targetClass == 17 || targetClass == 37 ||
        targetClass == 38 || targetClass == 39 || targetClass == 40;
    if (mechanical && classicConvertMechanical == false) return (false);
    return (true);
}
