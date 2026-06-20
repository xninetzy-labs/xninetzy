# Backward compatibility adapter. New code should import from app.xninetzy.os.style.store
import sys as _sys
import app.xninetzy.os.style.store as _mod
_sys.modules[__name__] = _mod
