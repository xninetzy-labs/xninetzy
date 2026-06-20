# Backward compatibility adapter. New code should import from app.xninetzy.interfaces.whatsapp.client
import sys as _sys
import app.xninetzy.interfaces.whatsapp.client as _mod
_sys.modules[__name__] = _mod
