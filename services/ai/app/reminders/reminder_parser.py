# Backward compatibility adapter. New code should import from app.xninetzy.os.reminders.reminder_parser
import sys as _sys
import app.xninetzy.os.reminders.reminder_parser as _mod
_sys.modules[__name__] = _mod
