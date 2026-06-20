# Backward compatibility adapter. New code should import from app.xninetzy.workflow.tools
import sys as _sys
import app.xninetzy.workflow.tools as _mod
_sys.modules[__name__] = _mod
