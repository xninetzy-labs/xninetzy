# Backward compatibility adapter. New code should import from app.xninetzy.schemas.routing
import sys as _sys
import app.xninetzy.schemas.routing as _mod
_sys.modules[__name__] = _mod
