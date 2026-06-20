# Backward compatibility adapter. New code should import from app.xninetzy.os.life.task_manager
import sys as _sys
import app.xninetzy.os.life.task_manager as _mod
_sys.modules[__name__] = _mod
