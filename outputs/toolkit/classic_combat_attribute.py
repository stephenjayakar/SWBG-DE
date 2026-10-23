"""Original ordered combat-table modifications, not DE effect emulation."""
from classic_air_model import f32


def modify(entries, mode, encoded):
    assert mode in (0, 4, 5)
    encoded = int(f32(encoded))
    selector, amount = (encoded >> 8) & 255, encoded & 255
    result = list(entries)
    index = selector if mode == 0 else next((i for i, (c, _) in enumerate(entries) if c == selector), len(entries))
    if index >= len(entries):
        return result
    cls, before = entries[index]
    value = amount if mode == 0 else before + amount if mode == 4 else int(before * amount * f32(0.01) + 0.5)
    result[index] = (cls, (value + 32768) % 65536 - 32768)
    return result
