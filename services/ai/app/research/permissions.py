# Backward compatibility adapter. New code should import from app.xninetzy.os.research.permissions
import sys as _sys
import app.xninetzy.os.research.permissions as _mod
_sys.modules[__name__] = _mod
