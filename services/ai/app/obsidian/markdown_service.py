# Backward compatibility adapter. New code should import from app.xninetzy.os.notes.markdown_service
import sys as _sys
import app.xninetzy.os.notes.markdown_service as _mod
_sys.modules[__name__] = _mod
