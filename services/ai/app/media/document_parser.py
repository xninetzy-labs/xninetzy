# Backward compatibility adapter. New code should import from app.xninetzy.interfaces.media.document_parser
import sys as _sys
import app.xninetzy.interfaces.media.document_parser as _mod
_sys.modules[__name__] = _mod
