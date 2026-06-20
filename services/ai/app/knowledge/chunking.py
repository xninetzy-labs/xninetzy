# Backward compatibility adapter. New code should import from app.xninetzy.os.knowledge.chunking
import sys as _sys
import app.xninetzy.os.knowledge.chunking as _mod
_sys.modules[__name__] = _mod
