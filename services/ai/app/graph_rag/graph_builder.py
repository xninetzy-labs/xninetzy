# Backward compatibility adapter. New code should import from app.xninetzy.os.graph.graph_builder
import sys as _sys
import app.xninetzy.os.graph.graph_builder as _mod
_sys.modules[__name__] = _mod
