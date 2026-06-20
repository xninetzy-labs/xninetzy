# Backward compatibility adapter. New code should import from app.xninetzy.os.academic.hebat.moodle_client
import sys as _sys
import app.xninetzy.os.academic.hebat.moodle_client as _mod
_sys.modules[__name__] = _mod
