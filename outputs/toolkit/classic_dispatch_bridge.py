"""Bounded PER callbacks for the development dispatch bridge; not installed.

The caller must call classicBridgeBegin with source-ordered pools first.
These blocks do not replace attack-now or enable an incomplete combat AI.
"""

OBSERVE = '''; Goals 112..114: one owned unit's native map zone at a time.
(defrule (true) =>
 (xs-script-call "swgbClassicDispatchObserveNext")
 (up-reset-search 1 1 1 1))
(defrule (up-compare-goal 112 c:> -1)
 (up-set-target-by-id g: 112) =>
 (up-get-object-data object-data-map-zone-id 113)
 (set-goal 114 1)
 (up-reset-search 1 1 1 1))
(defrule (up-compare-goal 114 c:== 1) =>
 (xs-script-call "swgbClassicDispatchObserveCommit"))
(defrule (up-compare-goal 112 c:> -1) => (up-jump-rule -4))
(defrule (true) => (up-reset-search 1 1 1 1))
'''

STOP = '''; Native owner check immediately before the stop request.
(defrule (true) =>
 (xs-script-call "swgbClassicDispatchStopNext")
 (up-reset-search 1 1 1 1))
(defrule (up-compare-goal 115 c:> -1)
 (up-set-target-by-id g: 115) =>
 (up-get-object-data object-data-player 118)
 (up-reset-search 1 1 1 1))
(defrule (up-compare-goal 115 c:> -1)
 (up-compare-goal 118 g:== 104) =>
 (up-add-object-by-id search-local g: 115)
 (up-target-point 116 action-stop -1 -1)
 (up-reset-search 1 1 1 1))
(defrule (up-compare-goal 115 c:> -1) => (up-jump-rule -4))
(defrule (true) => (up-reset-search 1 1 1 1))
'''
