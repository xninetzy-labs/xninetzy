# Backward compatibility adapter. New code should import from app.xninetzy.skills.graph_rag.prompts
import sys as _sys
import app.xninetzy.skills.graph_rag.prompts as _mod
_sys.modules[__name__] = _mod
