# Backward compatibility adapter. New code should import from app.xninetzy.os.reminders.reminder_policy
import sys as _sys
import app.xninetzy.os.reminders.reminder_policy as _mod
_sys.modules[__name__] = _mod
