# Backward compatibility adapter. New code should import from app.xninetzy.os.hitl.approval_service
import sys as _sys
import app.xninetzy.os.hitl.approval_service as _mod
_sys.modules[__name__] = _mod
