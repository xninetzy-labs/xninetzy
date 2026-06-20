# Backward compatibility adapter. New code should import from app.xninetzy.os.lightning.feedback_parser
import sys as _sys
import app.xninetzy.os.lightning.feedback_parser as _mod
_sys.modules[__name__] = _mod
