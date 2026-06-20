# Backward compatibility adapter. New code should import from app.xninetzy.os.research.actions.plan
import sys as _sys
import app.xninetzy.os.research.actions.plan as _mod
_sys.modules[__name__] = _mod
