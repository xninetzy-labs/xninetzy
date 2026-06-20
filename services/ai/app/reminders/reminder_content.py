# Backward compatibility adapter. New code should import from app.xninetzy.os.reminders.reminder_content
import sys as _sys
import app.xninetzy.os.reminders.reminder_content as _mod
_sys.modules[__name__] = _mod
