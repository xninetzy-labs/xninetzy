# Backward compatibility adapter. New code should import from app.xninetzy.os.lightning.service
import sys as _sys
import app.xninetzy.os.lightning.service as _mod
_sys.modules[__name__] = _mod
