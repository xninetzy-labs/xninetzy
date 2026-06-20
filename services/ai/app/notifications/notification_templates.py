# Backward compatibility adapter. New code should import from app.xninetzy.os.notifications.notification_templates
import sys as _sys
import app.xninetzy.os.notifications.notification_templates as _mod
_sys.modules[__name__] = _mod
