# Backward compatibility adapter. New code should import from app.xninetzy.interfaces.whatsapp.messaging
import sys as _sys
import app.xninetzy.interfaces.whatsapp.messaging as _mod
_sys.modules[__name__] = _mod
