# Backward compatibility adapter. New code should import from app.xninetzy.interfaces.api.deps.auth
import sys as _sys
import app.xninetzy.interfaces.api.deps.auth as _mod
_sys.modules[__name__] = _mod
