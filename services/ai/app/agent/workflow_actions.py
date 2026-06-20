# Backward compatibility adapter. New code should import from app.xninetzy.workflow.actions
import sys as _sys
import app.xninetzy.workflow.actions as _mod
_sys.modules[__name__] = _mod
