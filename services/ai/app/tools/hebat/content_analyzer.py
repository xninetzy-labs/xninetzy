# Backward compatibility adapter. New code should import from app.xninetzy.os.academic.hebat.content_analyzer
import sys as _sys
import app.xninetzy.os.academic.hebat.content_analyzer as _mod
_sys.modules[__name__] = _mod
