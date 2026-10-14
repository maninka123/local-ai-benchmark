"""Retry temporary Windows sharing locks when replacing workspace JSON files.

The benchmark prompts, scoring and inference settings are unchanged. Atomic
replacement preserves the previous complete file until the new save succeeds.
"""
import time,os,shutil
from pathlib import Path
from contextlib import contextmanager
from unittest.mock import patch


def extended_path(path):
    value=os.fspath(path)
    if os.name!='nt':return value
    value=os.path.abspath(value)
    if value.startswith('\\\\?\\'):return value
    return '\\\\?\\UNC\\'+value[2:] if value.startswith('\\\\') else '\\\\?\\'+value


@contextmanager
def long_file_copies():
    original=shutil.copy2
    def copy(source,target,*,follow_symlinks=True):
        return original(extended_path(source),extended_path(target),follow_symlinks=follow_symlinks)
    with patch.object(shutil,'copy2',copy):yield


@contextmanager
def atomic_replacements(root):
    original=Path.replace
    root=Path(root).resolve()
    def replace(source,target):
        target_path=Path(target)
        eligible=(source.name.startswith('.') and source.suffix=='.tmp'
                  and target_path.suffix=='.json' and target_path.resolve().is_relative_to(root))
        deadline=time.monotonic()+5
        delay=0.025
        while True:
            try:return original(source,target)
            except PermissionError as error:
                if not eligible or getattr(error,'winerror',None) not in (5,32,33) or time.monotonic()>=deadline:raise
                time.sleep(min(delay,max(0,deadline-time.monotonic())))
                delay=min(delay*2,0.5)
    with patch.object(Path,'replace',replace):yield
