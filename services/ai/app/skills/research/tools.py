# Backward compatibility adapter. New code should import from app.xninetzy.skills.research.tools
import sys as _sys
import app.xninetzy.skills.research.tools as _mod
_sys.modules[__name__] = _mod
