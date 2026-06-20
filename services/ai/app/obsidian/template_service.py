# Backward compatibility adapter. New code should import from app.xninetzy.os.notes.template_service
import sys as _sys
import app.xninetzy.os.notes.template_service as _mod
_sys.modules[__name__] = _mod
