# Backward compatibility adapter. New code should import from app.xninetzy.schemas.chat
import sys as _sys
import app.xninetzy.schemas.chat as _mod
_sys.modules[__name__] = _mod
