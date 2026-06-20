# Backward compatibility adapter. New code should import from app.xninetzy.os.knowledge.embeddings
import sys as _sys
import app.xninetzy.os.knowledge.embeddings as _mod
_sys.modules[__name__] = _mod
