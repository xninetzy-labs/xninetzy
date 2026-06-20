# Backward compatibility adapter. New code should import from app.xninetzy.os.life.goal_manager
import sys as _sys
import app.xninetzy.os.life.goal_manager as _mod
_sys.modules[__name__] = _mod
