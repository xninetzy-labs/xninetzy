# Backward compatibility adapter. New code should import from app.xninetzy.skills.obsidian.tools
import sys as _sys
import app.xninetzy.skills.obsidian.tools as _mod
_sys.modules[__name__] = _mod
