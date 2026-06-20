# Backward compatibility adapter. New code should import from app.xninetzy.tools.registry
import sys as _sys
import app.xninetzy.tools.registry as _mod
_sys.modules[__name__] = _mod
