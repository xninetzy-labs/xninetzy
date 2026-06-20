# Backward compatibility adapter. New code should import from app.xninetzy.tools.internal.obsidian
import sys as _sys
import app.xninetzy.tools.internal.obsidian as _mod
_sys.modules[__name__] = _mod
