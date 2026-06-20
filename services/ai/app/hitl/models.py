# Backward compatibility adapter. New code should import from app.xninetzy.os.hitl.models
import sys as _sys
import app.xninetzy.os.hitl.models as _mod
_sys.modules[__name__] = _mod
