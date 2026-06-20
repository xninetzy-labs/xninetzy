# Backward compatibility adapter. New code should import from app.xninetzy.os.rules.store
import sys as _sys
import app.xninetzy.os.rules.store as _mod
_sys.modules[__name__] = _mod
