# Backward compatibility adapter. New code should import from app.xninetzy.os.academic.hebat.html_cleaner
import sys as _sys
import app.xninetzy.os.academic.hebat.html_cleaner as _mod
_sys.modules[__name__] = _mod
