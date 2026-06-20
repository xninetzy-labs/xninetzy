# Backward compatibility adapter. New code should import from app.xninetzy.skills.graph_rag.tools
import sys as _sys
import app.xninetzy.skills.graph_rag.tools as _mod
_sys.modules[__name__] = _mod
