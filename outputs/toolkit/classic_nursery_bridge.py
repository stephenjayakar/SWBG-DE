"""Generate the bounded PER/XS nursery command bridge, retaining source rules."""

PER = '''; Isolated nine-rule loop. Do not insert conditional load directives here.
; Source animal decisions are independent of the Computer Classic rule graph.
(defrule (true) => (xs-script-call "swgbClassicNurseryBegin"))
(defrule (true) =>
 (xs-script-call "swgbClassicNurseryNext")
 (up-reset-search 1 1 1 1))
(defrule (up-compare-goal 106 c:> -1)
 (up-set-target-by-id g: 106) =>
 (up-get-object-data object-data-action 109)
 (up-get-object-data object-data-order 110)
 (up-reset-search 1 1 1 1))
(defrule (up-compare-goal 106 c:> -1)
 (up-compare-goal 109 c:== -1) (up-compare-goal 110 c:== -1) =>
 (xs-script-call "swgbClassicNurseryChoose"))
(defrule (up-compare-goal 107 c:> -1) (up-compare-goal 108 c:== 7)
 (up-set-target-by-id g: 107) =>
 (up-get-object-data object-data-garrison-count 111)
 (xs-script-call "swgbClassicNurseryCapacity")
 (up-reset-search 1 1 1 1))
(defrule (up-compare-goal 107 c:> -1) (up-compare-goal 108 c:== 7)
 (up-set-target-by-id g: 107) =>
 (up-reset-search 1 1 1 1)
 (up-add-object-by-id search-local g: 106)
 (up-target-objects 1 action-garrison -1 -1)
 (up-reset-search 1 1 1 1))
(defrule (up-compare-goal 107 c:> -1) (up-compare-goal 108 c:== 1)
 (up-set-target-by-id g: 107) =>
 (up-reset-search 1 1 1 1)
 (up-add-object-by-id search-local g: 106)
 (up-target-objects 1 action-move -1 -1)
 (up-reset-search 1 1 1 1))
(defrule (up-compare-goal 106 c:> -1) => (up-jump-rule -7))
(defrule (true) => (up-reset-search 1 1 1 1))
'''


def bridge_rules():
    # UP deltas are relative to the NEXT rule: 7 + 1 - 7 = 1.
    # The only backwards jump is from rule 7 to rule 1. Next always advances
    # the bounded queue cursor; the exhausted queue clears goal 106 to exit.
    assert PER.count('(defrule') == 9
    return PER
