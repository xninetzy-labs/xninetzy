# Backward compatibility adapter. New code should import from app.xninetzy.interfaces.media.media_store
import sys as _sys
import app.xninetzy.interfaces.media.media_store as _mod
_sys.modules[__name__] = _mod
