# Backward compatibility adapter. New code should import from app.xninetzy.os.life.workout_manager
import sys as _sys
import app.xninetzy.os.life.workout_manager as _mod
_sys.modules[__name__] = _mod
