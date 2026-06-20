# Backward compatibility adapter. New code should import from app.xninetzy.helper.command_docs
import sys as _sys
import app.xninetzy.helper.command_docs as _mod
_sys.modules[__name__] = _mod
