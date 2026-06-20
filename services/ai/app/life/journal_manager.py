# Backward compatibility adapter. New code should import from app.xninetzy.os.life.journal_manager
import sys as _sys
import app.xninetzy.os.life.journal_manager as _mod
_sys.modules[__name__] = _mod
