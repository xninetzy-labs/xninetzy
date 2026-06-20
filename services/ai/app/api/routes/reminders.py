# Backward compatibility adapter. New code should import from app.xninetzy.interfaces.api.routes.reminders
import sys as _sys
import app.xninetzy.interfaces.api.routes.reminders as _mod
_sys.modules[__name__] = _mod
