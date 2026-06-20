# Backward compatibility adapter. New code should import from app.xninetzy.agent.orchestrator
import sys as _sys
import app.xninetzy.agent.orchestrator as _mod
_sys.modules[__name__] = _mod
