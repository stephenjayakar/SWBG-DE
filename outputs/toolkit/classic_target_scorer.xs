// Source target scoring (0x592980), followed by classic_target_ranker.xs.
// Inputs are admitted targets with source combat estimates and countdowns.
// This component does not observe enemies or issue orders.
int classicScoreValues = -1;
int classicScoreModes = -1;
int classicScoreComponents = -1;
bool classicScoreRegicide = false;
int classicScoreSpecial1 = -1;
int classicScoreSpecial2 = -1;
int classicScoreSpecial3 = -1;
float classicScoreHi = 0.0;
float classicScoreLo = 0.0;

// Keep the low part of arithmetic that the original executes in x87 registers.
// Every local is deliberately separate to prevent loss before the final store.
void classicScoreAddWide(float a = 0.0, float b = 0.0) {
    float s = a + b;
    float v = s - a;
    float left = a - (s - v);
    float right = b - v;
    classicScoreHi = s;
    classicScoreLo = left + right;
}
void classicScoreMultiplyWide(float a = 0.0, float b = 0.0) {
    float p = a * b;
    float splitA = 4097.0 * a;
    float highA = splitA - (splitA - a);
    float lowA = a - highA;
    float splitB = 4097.0 * b;
    float highB = splitB - (splitB - b);
    float lowB = b - highB;
    float error = highA * highB - p;
    error = error + highA * lowB;
    error = error + lowA * highB;
    error = error + lowA * lowB;
    classicScoreHi = p;
    classicScoreLo = error;
}
float classicScoreRoundResidual(float base = 1.0, float residual = 0.0, float tail = 0.0) {
    // x87's 64-bit significand discards extremely small residuals. Preserve
    // round-to-nearest-even at that boundary instead of retaining extra bits
    // which would become a spurious nonzero score after subtracting from 25.
    if (residual == 0.0 && tail == 0.0) return(0.0);
    float magnitude = base;
    if (magnitude < 0.0) magnitude = 0.0 - magnitude;
    if (magnitude == 0.0) return(residual);
    float quantum = 0.000000000000000000108420217248550443400745280086994171142578125;
    for (scale = 0; < 256) {
        if (magnitude >= 2.0) {
            magnitude = magnitude * 0.5;
            quantum = quantum * 2.0;
        } else if (magnitude < 1.0) {
            magnitude = magnitude * 2.0;
            quantum = quantum * 0.5;
        } else break;
    }
    if (magnitude == 1.0 && residual < 0.0) quantum = quantum * 0.5;
    if (quantum == 0.0) return(residual);
    float units = residual / quantum;
    // Larger float residuals already have no bits below this quantum.
    if (units > 8388608.0 || units < -8388608.0) return(residual);
    int lower = 0 - xsCeilToInt(0.0 - units);
    float fraction = units - lower;
    bool roundUp = fraction > 0.5;
    if (fraction == 0.5) {
        roundUp = tail > 0.0 || (tail == 0.0 && lower % 2 != 0);
    }
    if (roundUp) lower++;
    return(quantum * lower);
}
float classicScoreWeightedFraction(float value = 0.0, float minimum = 0.0, float range = 1.0) {
    // Exact power-of-two scaling keeps the multiplication split finite even
    // when a combat estimate is the source FLOAT_MAX unreachable sentinel.
    for (scale = 0; < 128) {
        if (value <= 1.0 && minimum <= 1.0 && range <= 1.0) break;
        value = value * 0.5;
        minimum = minimum * 0.5;
        range = range * 0.5;
    }
    classicScoreAddWide(value, 0.0 - minimum);
    float numeratorHi = classicScoreHi;
    float numeratorLo = classicScoreRoundResidual(numeratorHi, classicScoreLo);
    float quotient = numeratorHi / range;
    classicScoreMultiplyWide(quotient, range);
    float productHi = classicScoreHi;
    float productLo = classicScoreLo;
    classicScoreAddWide(numeratorHi, 0.0 - productHi);
    float residualHi = classicScoreHi;
    float residualLo = classicScoreLo + (numeratorLo - productLo);
    classicScoreAddWide(residualHi, residualLo);
    residualHi = classicScoreHi;
    residualLo = classicScoreLo;
    float correction = residualHi / range;
    classicScoreMultiplyWide(correction, range);
    float tail = residualHi - classicScoreHi;
    tail = tail + (residualLo - classicScoreLo);
    tail = tail / range;
    if (quotient == 1.0 && correction < 0.0000000000001 && correction > -0.0000000000001) {
        float rounded = classicScoreRoundResidual(quotient, correction, tail);
        classicScoreMultiplyWide(rounded, 25.0);
        return(0.0 - classicScoreRoundResidual(25.0, classicScoreHi, classicScoreLo));
    }
    classicScoreMultiplyWide(quotient, 25.0);
    productHi = classicScoreHi;
    productLo = classicScoreLo;
    classicScoreMultiplyWide(correction, 25.0);
    float correctionHi = classicScoreHi;
    float correctionLo = classicScoreLo;
    classicScoreAddWide(25.0, 0.0 - productHi);
    float high = classicScoreHi;
    float low = classicScoreLo - productLo;
    classicScoreAddWide(high, 0.0 - correctionHi);
    low = low + classicScoreLo;
    low = low - correctionLo;
    low = low - tail * 25.0;
    return(classicScoreHi + low);
}

void classicScoreReset(bool regicide = false, int special1 = -1, int special2 = -1, int special3 = -1) {
    classicTargetReset();
    if (classicScoreValues < 0) {
        classicScoreValues = xsArrayCreateFloat(3072, 0.0, "classic target metrics");
        classicScoreModes = xsArrayCreateInt(1024, 0, "classic target priorities");
        classicScoreComponents = xsArrayCreateFloat(4096, 0.0, "classic score components");
    }
    classicScoreRegicide = regicide;
    classicScoreSpecial1 = special1;
    classicScoreSpecial2 = special2;
    classicScoreSpecial3 = special3;
}

void classicScoreAdd(int unit = -1, int sourceClass = 32, int sourceId = 4,
    float ttk = 10.0, float ttbk = 10.0, float distance = 20.0, bool sameZone = true,
    bool alive = true, bool relicCountdown = false, bool carriesRelic = false, bool wonderCountdown = false) {
    if (classicTargetCount >= 1024) return;
    int index = classicTargetCount;
    classicTargetAdd(unit, 0.0, false, sourceClass, sourceId, sameZone);
    xsArraySetFloat(classicScoreValues, index * 3, ttk);
    xsArraySetFloat(classicScoreValues, index * 3 + 1, ttbk);
    xsArraySetFloat(classicScoreValues, index * 3 + 2, distance);
    // 0 regular, 1 priority100, 2 priority99.9, 3 gone, 4 ordinary wall.
    int mode = 0;
    if (sourceClass == 6) mode = 4;
    if (ttk < 340282346638528859811704183484516925440.0) {
        if (classicScoreRegicide && sourceClass == 46) mode = 1;
        else if (relicCountdown && (sourceClass == 51 || sourceId == 104)) {
            mode = 2;
            if (carriesRelic) mode = 1;
        } else if (sourceId == 104 && classicScoreSpecial1 == 1) mode = 1;
        else if (sourceClass == 8 && classicScoreSpecial2 == 1) mode = 1;
        else if (sourceId == 276 && (classicScoreSpecial3 == 1 || wonderCountdown)) mode = 1;
    }
    if (alive == false) mode = 3;
    xsArraySetInt(classicScoreModes, index, mode);
}

void classicScoreEvaluate() {
    if (classicTargetCount <= 0) {
        classicTargetRank();
        return;
    }
    float minKill = xsArrayGetFloat(classicScoreValues, 0);
    float maxKill = minKill;
    float minSurvival = xsArrayGetFloat(classicScoreValues, 1);
    float maxSurvival = minSurvival;
    float minDistance = xsArrayGetFloat(classicScoreValues, 2);
    float maxDistance = minDistance;
    for (i = 1; < classicTargetCount) {
        float killValue = xsArrayGetFloat(classicScoreValues, i * 3);
        float survivalValue = xsArrayGetFloat(classicScoreValues, i * 3 + 1);
        float distanceValue = xsArrayGetFloat(classicScoreValues, i * 3 + 2);
        if (killValue < minKill) minKill = killValue;
        if (killValue > maxKill) maxKill = killValue;
        if (survivalValue < minSurvival) minSurvival = survivalValue;
        if (survivalValue > maxSurvival) maxSurvival = survivalValue;
        if (distanceValue < minDistance) minDistance = distanceValue;
        if (distanceValue > maxDistance) maxDistance = distanceValue;
    }
    float killRange = maxKill - minKill;
    float survivalRange = maxSurvival - minSurvival;
    float distanceRange = maxDistance - minDistance;
    for (i = 0; < classicTargetCount) {
        int mode = xsArrayGetInt(classicScoreModes, i);
        float score = 0.0;
        bool unordered = false;
        xsArraySetFloat(classicScoreComponents, i * 4, 0.0);
        xsArraySetFloat(classicScoreComponents, i * 4 + 1, 0.0);
        xsArraySetFloat(classicScoreComponents, i * 4 + 2, 0.0);
        xsArraySetFloat(classicScoreComponents, i * 4 + 3, 0.0);
        if (mode == 1) score = 100.0;
        else if (mode == 2) score = 99.9;
        else if (mode != 3) {
            float kill = 25.0;
            float survival = 25.0;
            float proximity = 25.0;
            float ttk = xsArrayGetFloat(classicScoreValues, i * 3);
            if (killRange >= 0.0000001) kill = classicScoreWeightedFraction(ttk, minKill, killRange);
            // Original bug: survival's gate uses TTBK, but its expression reuses
            // TTK. Represent the zero-denominator NaN explicitly for the ranker.
            if (survivalRange >= 0.0000001) {
                if (killRange == 0.0) unordered = true;
                else survival = classicScoreWeightedFraction(ttk, minKill, killRange);
            }
            if (distanceRange >= 0.0000001)
                proximity = classicScoreWeightedFraction(xsArrayGetFloat(classicScoreValues, i * 3 + 2), minDistance, distanceRange);
            classicScoreAddWide(proximity, kill);
            float high = classicScoreHi;
            float low = classicScoreLo;
            float zone = 0.0;
            if (xsArrayGetBool(classicTargetSameZone, i)) zone = 25.0;
            xsArraySetFloat(classicScoreComponents, i * 4, kill);
            xsArraySetFloat(classicScoreComponents, i * 4 + 1, survival);
            xsArraySetFloat(classicScoreComponents, i * 4 + 2, proximity);
            xsArraySetFloat(classicScoreComponents, i * 4 + 3, zone);
            classicScoreAddWide(high, zone);
            high = classicScoreHi;
            low = low + classicScoreLo;
            classicScoreAddWide(high, survival);
            low = low + classicScoreLo;
            score = classicScoreHi + low;
            if (mode == 4 && score >= 100.0 && unordered == false) score = 99.0;
        }
        xsArraySetFloat(classicTargetScores, i, score);
        xsArraySetBool(classicTargetUnordered, i, unordered);
    }
    classicTargetRank();
}
