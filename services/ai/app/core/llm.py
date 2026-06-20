# Backward compatibility adapter. New code should import from app.xninetzy.core.llm
import sys as _sys
import app.xninetzy.core.llm as _mod
_sys.modules[__name__] = _mod
