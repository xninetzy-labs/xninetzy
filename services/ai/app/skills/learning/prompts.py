# Backward compatibility adapter. New code should import from app.xninetzy.skills.learning.prompts
import sys as _sys
import app.xninetzy.skills.learning.prompts as _mod
_sys.modules[__name__] = _mod
