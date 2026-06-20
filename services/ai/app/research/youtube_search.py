# Backward compatibility adapter. New code should import from app.xninetzy.os.research.youtube_search
import sys as _sys
import app.xninetzy.os.research.youtube_search as _mod
_sys.modules[__name__] = _mod
