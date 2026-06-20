# Backward compatibility adapter. New code should import from app.xninetzy.os.graph.graph_store
import sys as _sys
import app.xninetzy.os.graph.graph_store as _mod
_sys.modules[__name__] = _mod
