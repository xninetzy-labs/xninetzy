# Backward compatibility adapter. New code should import from app.xninetzy.skills.hebat.tools
import sys as _sys
import app.xninetzy.skills.hebat.tools as _mod
_sys.modules[__name__] = _mod
