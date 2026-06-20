# Backward compatibility adapter. New code should import from app.xninetzy.agent.response
import sys as _sys
import app.xninetzy.agent.response as _mod
_sys.modules[__name__] = _mod
