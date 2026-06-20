# Backward compatibility adapter. New code should import from app.xninetzy.ecosystem.event_bus
import sys as _sys
import app.xninetzy.ecosystem.event_bus as _mod
_sys.modules[__name__] = _mod
