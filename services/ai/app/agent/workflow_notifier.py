# Backward compatibility adapter. New code should import from app.xninetzy.workflow.notifier
import sys as _sys
import app.xninetzy.workflow.notifier as _mod
_sys.modules[__name__] = _mod
