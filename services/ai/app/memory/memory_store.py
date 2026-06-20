# Backward compatibility adapter. New code should import from app.xninetzy.os.memory.memory_store
import sys as _sys
import app.xninetzy.os.memory.memory_store as _mod
_sys.modules[__name__] = _mod
