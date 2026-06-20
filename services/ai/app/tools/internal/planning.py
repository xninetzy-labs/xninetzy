# Backward compatibility adapter. New code should import from app.xninetzy.tools.internal.planning
import sys as _sys
import app.xninetzy.tools.internal.planning as _mod
_sys.modules[__name__] = _mod
