# Backward compatibility adapter. New code should import from app.xninetzy.interfaces.media.media_tools
import sys as _sys
import app.xninetzy.interfaces.media.media_tools as _mod
_sys.modules[__name__] = _mod
