# Backward compatibility adapter. New code should import from app.xninetzy.tools.ecosystem.life_tools
import sys as _sys
import app.xninetzy.tools.ecosystem.life_tools as _mod
_sys.modules[__name__] = _mod
