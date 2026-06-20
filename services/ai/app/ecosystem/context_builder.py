# Backward compatibility adapter. New code should import from app.xninetzy.ecosystem.context_builder
import sys as _sys
import app.xninetzy.ecosystem.context_builder as _mod
_sys.modules[__name__] = _mod
