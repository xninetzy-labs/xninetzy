# Backward compatibility adapter. New code should import from app.xninetzy.os.rules.tools
import sys as _sys
import app.xninetzy.os.rules.tools as _mod
_sys.modules[__name__] = _mod
