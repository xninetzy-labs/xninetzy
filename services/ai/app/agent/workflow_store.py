# Backward compatibility adapter. New code should import from app.xninetzy.workflow.store
import sys as _sys
import app.xninetzy.workflow.store as _mod
_sys.modules[__name__] = _mod
