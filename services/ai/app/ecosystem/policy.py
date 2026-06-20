# Backward compatibility adapter. New code should import from app.xninetzy.ecosystem.policy
import sys as _sys
import app.xninetzy.ecosystem.policy as _mod
_sys.modules[__name__] = _mod
