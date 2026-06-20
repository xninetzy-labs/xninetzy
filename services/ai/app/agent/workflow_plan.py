# Backward compatibility adapter. New code should import from app.xninetzy.workflow.plan
import sys as _sys
import app.xninetzy.workflow.plan as _mod
_sys.modules[__name__] = _mod
