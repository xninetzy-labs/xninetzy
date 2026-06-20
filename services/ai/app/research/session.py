# Backward compatibility adapter. New code should import from app.xninetzy.os.research.session
import sys as _sys
import app.xninetzy.os.research.session as _mod
_sys.modules[__name__] = _mod
