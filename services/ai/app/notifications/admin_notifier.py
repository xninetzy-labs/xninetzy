# Backward compatibility adapter. New code should import from app.xninetzy.os.notifications.admin_notifier
import sys as _sys
import app.xninetzy.os.notifications.admin_notifier as _mod
_sys.modules[__name__] = _mod
