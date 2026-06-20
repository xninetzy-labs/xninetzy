# Backward compatibility adapter. New code should import from app.xninetzy.skills.hebat.prompts
import sys as _sys
import app.xninetzy.skills.hebat.prompts as _mod
_sys.modules[__name__] = _mod
