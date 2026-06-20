# Backward compatibility adapter. New code should import from app.xninetzy.os.graph.models
import sys as _sys
import app.xninetzy.os.graph.models as _mod
_sys.modules[__name__] = _mod
