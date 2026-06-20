# Backward compatibility adapter. New code should import from app.xninetzy.os.academic.hebat.download_resolver
import sys as _sys
import app.xninetzy.os.academic.hebat.download_resolver as _mod
_sys.modules[__name__] = _mod
