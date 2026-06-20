# Backward compatibility adapter. New code should import from app.xninetzy.skills.learning.tools
import sys as _sys
import app.xninetzy.skills.learning.tools as _mod
_sys.modules[__name__] = _mod
