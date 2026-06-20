# Backward compatibility adapter. New code should import from app.xninetzy.skills.models
import sys as _sys
import app.xninetzy.skills.models as _mod
_sys.modules[__name__] = _mod
