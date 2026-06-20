# Backward compatibility adapter. New code should import from app.xninetzy.db.sqlite
import sys as _sys
import app.xninetzy.db.sqlite as _mod
_sys.modules[__name__] = _mod
