# Backward compatibility adapter. New code should import from app.xninetzy.workflow.models
import sys as _sys
import app.xninetzy.workflow.models as _mod
_sys.modules[__name__] = _mod
