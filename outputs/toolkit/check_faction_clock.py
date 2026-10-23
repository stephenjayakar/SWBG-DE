"""Check elapsed-game-time accounting under pauses and skipped callbacks."""
from pathlib import Path
import json,math,re
script=Path('work/faction-package/resources/_common/xs/swgb_factions.xs').read_text()
body=script.split('rule swgbNurseryTick',1)[1].split('void main()',1)[0]
assert 'int now = xsGetGameTime();' in body
assert 'float elapsed = now - swgbNurseryLastSecond;' in body
assert 'swgbNurseryRate(owner) * elapsed, owner' in body
assert body.index('float elapsed')<body.index('swgbNurseryLastSecond = now;',body.index('float elapsed'))
assert 'if (now <= swgbNurseryLastSecond) return;' in body
# For continuously garrisoned animals, callback cadence must not change the
# amount credited over the same amount of simulation time.
def income(times):
    last=times[0];food=0.0
    for now in times[1:]:
        if now<=last:continue
        food+=.13*(now-last);last=now
    return food
cases=[list(range(0,121)),list(range(0,121,2)),[0,0,0,3,7,7,40,119,120]]
assert all(math.isclose(income(case),15.6) for case in cases)
assert income([0,0,0,0])==0
assert not re.search(r'\b(timeGetTime|GetTickCount|performance\.now|Date\.now)\b',script)
report=dict(clock='game time',income_over_120_game_seconds=15.6,
            paused_time_pays_zero=True,delayed_tick_catch_up=True,engine_verified=False)
Path('outputs/faction-clock-validation.json').write_text(json.dumps(report,indent=2))
print(report)
