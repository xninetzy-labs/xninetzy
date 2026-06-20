# Backward compatibility adapter. New code should import from app.xninetzy.agent.prompts
import sys as _sys
import app.xninetzy.agent.prompts as _mod
_sys.modules[__name__] = _mod
