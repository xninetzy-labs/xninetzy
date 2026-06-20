# Backward compatibility adapter. New code should import from app.xninetzy.ecosystem.command_router
import sys as _sys
import app.xninetzy.ecosystem.command_router as _mod
_sys.modules[__name__] = _mod
