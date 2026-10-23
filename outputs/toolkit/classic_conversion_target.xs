// Original bestUnitToConvert ordered selector (0x5B4E80).
// Feed the existing source LOS scan in order, including its byte distances.
// Caller supplies enemy relation, lookup/state and completed conversion gate.
// State/distance are already source bytes; HP/class are source signed shorts.
// No target discovery, Euclidean-distance substitution or conversion orders.
int classicConversionTargetID = -1;
float classicConversionTargetDistance = -123.0;
float classicConversionTargetScore = 0.0;
void classicConversionTargetReset(float initialDistance = -123.0) {
    classicConversionTargetID = -1;
    classicConversionTargetDistance = initialDistance;
    classicConversionTargetScore = 0.0;
}

// Compare exact short / small-integer ratio against the last stored float.
// The source's x87 ratio is wider than its float32 saved best value.
bool classicConversionRatioGreater(float hp = 0.0, float divisor = 1.0) {
    float best = classicConversionTargetScore;
    float product = best * divisor;
    float split = 4097.0 * best;
    float high = split - (split - best);
    float low = best - high;
    // Divisor <=259 is exactly representable; splitting it is unnecessary.
    float error = high * divisor - product;
    error = error + low * divisor;
    return(hp > product || (hp == product && error < 0.0));
}

void classicConversionTargetAdd(int unit = -1, bool enemy = false,
    bool present = false, int state = 3, bool convertible = false,
    int distanceByte = 1, int maxHP = 0, int sourceClass = -1) {
    if (enemy == false || present == false || state >= 3 || convertible == false) return;
    float distance = 1.0 * distanceByte;
    if (distance < 1.0) distance = 1.0;
    float divisor = distance;
    if (sourceClass == 47) divisor = divisor + 4.0;
    float hp = 1.0 * maxHP;
    if (classicConversionTargetID == -1 || classicConversionRatioGreater(hp, divisor)) {
        classicConversionTargetID = unit;
        classicConversionTargetDistance = distance;
        classicConversionTargetScore = hp / divisor;
    }
}
