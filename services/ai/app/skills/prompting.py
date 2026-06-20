# Backward compatibility adapter. New code should import from app.xninetzy.skills.prompting
import sys as _sys
import app.xninetzy.skills.prompting as _mod
_sys.modules[__name__] = _mod
