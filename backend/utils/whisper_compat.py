"""
Whisper / numba 与 coverage 的兼容性补丁

numba 0.64 在导入时会引用 coverage.types 中的若干符号（Tracer / TShouldTraceFn /
TShouldStartContextFn），而 coverage 7.4+ 已经重命名（Tracer → TracerCore）或移除
了这些符号。任何 `import whisper` 都会触发 numba 的连锁导入并抛 AttributeError。

调用 patch() 把 numba 期望的符号回填到 coverage.types 里，让后续 import whisper
能正常完成。必须在任何 `import whisper`、`import numba` 之前调用。
"""
from __future__ import annotations

from typing import Any


def patch() -> None:
    try:
        import coverage.types as _ct
    except ImportError:
        return

    aliases = {
        "Tracer": getattr(_ct, "TracerCore", Any),
        "TShouldTraceFn": Any,
        "TShouldStartContextFn": Any,
    }
    for name, value in aliases.items():
        if not hasattr(_ct, name):
            setattr(_ct, name, value)
