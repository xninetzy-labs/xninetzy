# Backward compatibility adapter. New code should import from app.xninetzy.skills.tools
import sys as _sys
import app.xninetzy.skills.tools as _mod
_sys.modules[__name__] = _mod
