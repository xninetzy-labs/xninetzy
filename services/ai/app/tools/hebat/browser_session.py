# Backward compatibility adapter. New code should import from app.xninetzy.os.academic.hebat.browser_session
import sys as _sys
import app.xninetzy.os.academic.hebat.browser_session as _mod
_sys.modules[__name__] = _mod
