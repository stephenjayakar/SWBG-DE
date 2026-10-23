// Source 0x4899B0/0x489B10/0x489D20 combat-table updates.
// Explicit caller-owned ordered class/value arrays, no native mutations.
// Encoded parameter is the source's truncated signed integer (finite input).
// Requires classic_target_scorer.xs wide-arithmetic helpers.
int classicAttributeSignedShort(int value = 0) {
    value = value % 65536;
    if (value < -32768) value = value + 65536;
    if (value > 32767) value = value - 65536;
    return(value);
}
int classicAttributeMultiply(int before = 0, int amount = 0) {
    // The original uses float32(0.01) in x87, adds 0.5, then truncates.
    // before*amount fits 24 bits exactly. Retain its fractional residual so
    // rounding to a float32 integer does not change the final truncation.
    float product = before * amount;
    classicScoreMultiplyWide(product, 0.00999999977648258209228515625);
    float high = classicScoreHi;
    float low = classicScoreLo;
    classicScoreAddWide(high, 0.5);
    high = classicScoreHi;
    low = low + classicScoreLo;
    int truncated = xsCeilToInt(high);
    if (high > 0.0) truncated = 0 - xsCeilToInt(0.0 - high);
    if (high == truncated) {
        if (high > 0.0 && low < 0.0) truncated--;
        if (high < 0.0 && low > 0.0) truncated++;
    }
    return(classicAttributeSignedShort(truncated));
}
bool classicAttributeModify(int classes = -1, int values = -1, int count = 0,
    int mode = 0, int encoded = 0) {
    if (classes < 0 || values < 0 || count < 0) return(false);
    if (count > xsArrayGetSize(classes) || count > xsArrayGetSize(values)) return(false);
    if (mode != 0 && mode != 4 && mode != 5) return(false);
    int packed = encoded % 65536;
    if (packed < 0) packed = packed + 65536;
    int selector = packed / 256;
    int amount = packed % 256;
    int index = selector;
    if (mode != 0) {
        index = count;
        for (i = 0; < count) {
            if (xsArrayGetInt(classes, i) == selector) { index = i; break; }
        }
    }
    // An absent class or out-of-range ordinal is a valid no-op. Source does
    // not append a table entry, and only the first duplicate is changed.
    if (index >= count) return(true);
    int before = xsArrayGetInt(values, index);
    int after = amount;
    if (mode == 4) after = classicAttributeSignedShort(before + amount);
    if (mode == 5) after = classicAttributeMultiply(before, amount);
    xsArraySetInt(values, index, after);
    return(true);
}
