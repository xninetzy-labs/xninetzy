# Backward compatibility adapter. New code should import from app.xninetzy.agent.graph
import sys as _sys
import app.xninetzy.agent.graph as _mod
_sys.modules[__name__] = _mod
