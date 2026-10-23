"""Read AI response text from the source language resources as data only."""
import ctypes
from ctypes import wintypes
from classic_ai_source import SOURCE

CHAT_BASE=920000


def source_strings(ids):
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    user=ctypes.WinDLL('user32')
    kernel.LoadLibraryExW.argtypes=[wintypes.LPCWSTR,wintypes.HANDLE,wintypes.DWORD]
    kernel.LoadLibraryExW.restype=wintypes.HMODULE
    kernel.FreeLibrary.argtypes=[wintypes.HMODULE]
    user.LoadStringW.argtypes=[wintypes.HINSTANCE,wintypes.UINT,wintypes.LPWSTR,ctypes.c_int]
    handles=[]
    try:
        # LOAD_LIBRARY_AS_DATAFILE cannot execute the DLL's entry point.
        for name in ('language.dll','language_x1.dll','language_x2.dll'):
            handle=kernel.LoadLibraryExW(str(SOURCE.parent/name),None,2)
            assert handle,name
            handles.append(handle)
        result={};buffer=ctypes.create_unicode_buffer(32768)
        for sid in sorted(ids):
            for handle in handles:
                if user.LoadStringW(handle,sid,buffer,len(buffer)):
                    result[sid]=buffer.value
        assert set(result)==set(ids),('Missing source chat strings',sorted(set(ids)-set(result)))
        return result
    finally:
        for handle in handles:kernel.FreeLibrary(handle)
