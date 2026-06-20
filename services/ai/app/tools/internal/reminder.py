# Backward compatibility adapter. New code should import from app.xninetzy.tools.internal.reminder
import sys as _sys
import app.xninetzy.tools.internal.reminder as _mod
_sys.modules[__name__] = _mod
