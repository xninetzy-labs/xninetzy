# Backward compatibility adapter. New code should import from app.xninetzy.os.research.deep_research
import sys as _sys
import app.xninetzy.os.research.deep_research as _mod
_sys.modules[__name__] = _mod
