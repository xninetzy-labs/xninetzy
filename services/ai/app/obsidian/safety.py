# Backward compatibility adapter. New code should import from app.xninetzy.os.notes.safety
import sys as _sys
import app.xninetzy.os.notes.safety as _mod
_sys.modules[__name__] = _mod
