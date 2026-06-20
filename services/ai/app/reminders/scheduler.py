# Backward compatibility adapter. New code should import from app.xninetzy.os.reminders.scheduler
import sys as _sys
import app.xninetzy.os.reminders.scheduler as _mod
_sys.modules[__name__] = _mod
