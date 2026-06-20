# Backward compatibility adapter. New code should import from app.xninetzy.os.knowledge.vector_store
import sys as _sys
import app.xninetzy.os.knowledge.vector_store as _mod
_sys.modules[__name__] = _mod
