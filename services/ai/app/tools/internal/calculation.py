# Backward compatibility adapter. New code should import from app.xninetzy.tools.internal.calculation
import sys as _sys
import app.xninetzy.tools.internal.calculation as _mod
_sys.modules[__name__] = _mod
