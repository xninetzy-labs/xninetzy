# Backward compatibility adapter. New code should import from app.xninetzy.os.graph.graph_context
import sys as _sys
import app.xninetzy.os.graph.graph_context as _mod
_sys.modules[__name__] = _mod
