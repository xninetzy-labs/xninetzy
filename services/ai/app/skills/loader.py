# Backward compatibility adapter. New code should import from app.xninetzy.skills.loader
import sys as _sys
import app.xninetzy.skills.loader as _mod
_sys.modules[__name__] = _mod
