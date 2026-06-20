# Backward compatibility adapter. New code should import from app.xninetzy.interfaces.api.routes.debug
import sys as _sys
import app.xninetzy.interfaces.api.routes.debug as _mod
_sys.modules[__name__] = _mod
