# Backward compatibility adapter. New code should import from app.xninetzy.tools.internal.datetime_info
import sys as _sys
import app.xninetzy.tools.internal.datetime_info as _mod
_sys.modules[__name__] = _mod
