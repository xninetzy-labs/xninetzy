# Backward compatibility adapter. New code should import from app.xninetzy.core.logging
import sys as _sys
import app.xninetzy.core.logging as _mod
_sys.modules[__name__] = _mod
