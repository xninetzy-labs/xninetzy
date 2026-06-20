# Backward compatibility adapter. New code should import from app.xninetzy.agent.executor
import sys as _sys
import app.xninetzy.agent.executor as _mod
_sys.modules[__name__] = _mod
