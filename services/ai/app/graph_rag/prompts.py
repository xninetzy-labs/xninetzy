# Backward compatibility adapter. New code should import from app.xninetzy.os.graph.prompts
import sys as _sys
import app.xninetzy.os.graph.prompts as _mod
_sys.modules[__name__] = _mod
