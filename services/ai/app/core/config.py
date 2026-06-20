# Backward compatibility adapter. New code should import from app.xninetzy.core.config
import sys as _sys
import app.xninetzy.core.config as _mod
_sys.modules[__name__] = _mod
