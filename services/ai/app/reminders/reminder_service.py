# Backward compatibility adapter. New code should import from app.xninetzy.os.reminders.reminder_service
import sys as _sys
import app.xninetzy.os.reminders.reminder_service as _mod
_sys.modules[__name__] = _mod
