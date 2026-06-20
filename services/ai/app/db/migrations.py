# Backward compatibility adapter. New code should import from app.xninetzy.db.migrations
import sys as _sys
import app.xninetzy.db.migrations as _mod
_sys.modules[__name__] = _mod
