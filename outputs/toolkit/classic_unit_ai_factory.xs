// Type indices follow classic_unit_ai_catalog.TYPES; -1 means no UnitAI.
// Inputs are source master class and source volley_missile_id (+0x1B8).
int classicUnitAIType(int sourceClass = -1, int volleyMissileID = -1) {
    if (sourceClass == 3 || sourceClass == 20 || sourceClass == 22 || sourceClass == 23 ||
        sourceClass == 24 || sourceClass == 25 || sourceClass == 26 || sourceClass == 27 ||
        sourceClass == 29 || sourceClass == 30 || sourceClass == 31 || sourceClass == 41 || sourceClass == 42) return (-1);
    if (sourceClass == 1) return (0);
    if (sourceClass == 4 || sourceClass == 46) return (1);
    if (sourceClass == 60) return (2);
    if (sourceClass == 5) return (3);
    if (sourceClass == 58) return (4);
    if (sourceClass == 54) return (5);
    if (sourceClass == 50 || sourceClass == 51) return (6);
    if (sourceClass == 12 || sourceClass == 45) return (7);
    if (sourceClass == 17 || sourceClass == 59) return (8);
    if (sourceClass == 14) return (9);
    if (sourceClass == 21 || sourceClass == 28) return (11);
    if (sourceClass == 11 || sourceClass == 16 || sourceClass == 32 || sourceClass == 33 ||
        sourceClass == 34 || sourceClass == 35 || sourceClass == 36 || sourceClass == 37 || sourceClass == 40) return (13);
    if (sourceClass == 6 || sourceClass == 7 || sourceClass == 8 || sourceClass == 9 || sourceClass == 10 || sourceClass == 18) {
        if (sourceClass == 9 || sourceClass == 10 || volleyMissileID >= 0) return (12);
        return (14);
    }
    return (10);
}

// Combat gate IDs follow the compiled eligibility pipeline (0..8), -1 absent.
int classicUnitAIAttackKind(int type = -1) {
    if (type == -1) return (-1);
    if (type == 14) return (1);
    if (type == 12) return (2);
    if (type == 10) return (3);
    if (type == 6) return (4);
    if (type == 13) return (5);
    if (type == 4) return (6);
    if (type == 3) return (7);
    if (type == 5) return (8);
    return (0);
}

int classicUnitAINeutralKind(int type = -1) {
    if (type == -1 || type == 4 || type == 5 || type == 14) return (4);
    if (type == 10 || type == 12) return (1);
    if (type == 6) return (2);
    if (type == 13) return (3);
    return (0);
}

bool classicUnitAIHasConversion(int type = -1) {
    return (type == 6);
}
