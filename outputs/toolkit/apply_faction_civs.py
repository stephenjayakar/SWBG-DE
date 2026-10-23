"""Apply faction_civs metadata to the installed Draft/Assets mods and outputs/SWGB-DE-Factions-Draft.

Run from the repo root. Reads the civ descriptions from the installed source language DLLs.
"""
import ctypes, json, re, sys
from ctypes import wintypes
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import faction_civs

GAME = Path(r'E:\GOG Games\Star Wars - Galactic Battlegrounds\Game')
LOCAL = Path(r'C:\Users\aj12a\Games\Age of Empires 2 DE\76561198022514833\mods\local')
DRAFTS = [LOCAL / 'SWGB-DE-Factions-Draft', Path('outputs/SWGB-DE-Factions-Draft')]
ASSETS = LOCAL / 'SWGB-DE-Factions-Assets'
STRINGS = ASSETS / 'resources/en/strings/key-value/key-value-modded-strings-utf8.txt'


def source_strings(ids):
    kernel = ctypes.WinDLL('kernel32', use_last_error=True); user = ctypes.WinDLL('user32', use_last_error=True)
    kernel.LoadLibraryExW.argtypes = [wintypes.LPCWSTR, wintypes.HANDLE, wintypes.DWORD]; kernel.LoadLibraryExW.restype = wintypes.HMODULE
    kernel.FreeLibrary.argtypes = [wintypes.HMODULE]
    user.LoadStringW.argtypes = [wintypes.HINSTANCE, wintypes.UINT, wintypes.LPWSTR, ctypes.c_int]
    buf = ctypes.create_unicode_buffer(32768); out = {}
    for name in ('language.dll', 'language_x1.dll', 'language_x2.dll'):  # later DLLs override, as in-game
        h = kernel.LoadLibraryExW(str(GAME / name), None, 2)
        if not h: raise ctypes.WinError(ctypes.get_last_error())
        try:
            for sid in ids:
                if user.LoadStringW(h, sid, buf, len(buf)): out[sid] = buf.value
        finally: kernel.FreeLibrary(h)
    return out


def main():
    civs = faction_civs.civilizations()
    for draft in DRAFTS:
        path = draft / 'resources/_common/dat/civilizations.json'
        path.write_text(json.dumps(civs, indent=2), encoding='utf-8')
        print('wrote', path)
        for p in faction_civs.write_images(ASSETS / 'widgetui/textures/ingame/units', draft / 'resources/_common/wpfg'):
            print('wrote', p)
    src = source_strings([f['source_desc_sid'] for f in faction_civs.FACTIONS])
    new = faction_civs.description_strings(src)
    lines = STRINGS.read_text(encoding='utf-8').splitlines()
    keep = [l for l in lines if not re.match(r'^(%s) ' % '|'.join(map(str, new)), l)]
    keep += [f'{sid} {json.dumps(text, ensure_ascii=False)}' for sid, text in sorted(new.items())]
    STRINGS.write_text('\n'.join(keep) + '\n', encoding='utf-8')
    print('strings', {k: v[:80] for k, v in new.items()})


if __name__ == '__main__':
    main()
