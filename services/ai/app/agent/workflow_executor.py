# Backward compatibility adapter. New code should import from app.xninetzy.workflow.executor
import sys as _sys
import app.xninetzy.workflow.executor as _mod
_sys.modules[__name__] = _mod
