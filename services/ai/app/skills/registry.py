# Backward compatibility adapter. New code should import from app.xninetzy.skills.registry
import sys as _sys
import app.xninetzy.skills.registry as _mod
_sys.modules[__name__] = _mod
