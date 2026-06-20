# Backward compatibility adapter. New code should import from app.xninetzy.agent.state
import sys as _sys
import app.xninetzy.agent.state as _mod
_sys.modules[__name__] = _mod
