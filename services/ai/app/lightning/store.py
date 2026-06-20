# Backward compatibility adapter. New code should import from app.xninetzy.os.lightning.store
import sys as _sys
import app.xninetzy.os.lightning.store as _mod
_sys.modules[__name__] = _mod
