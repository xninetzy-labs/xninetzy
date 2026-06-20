# Backward compatibility adapter. New code should import from app.xninetzy.os.research.actions.base
import sys as _sys
import app.xninetzy.os.research.actions.base as _mod
_sys.modules[__name__] = _mod
