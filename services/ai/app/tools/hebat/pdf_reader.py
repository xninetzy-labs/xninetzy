# Backward compatibility adapter. New code should import from app.xninetzy.os.academic.hebat.pdf_reader
import sys as _sys
import app.xninetzy.os.academic.hebat.pdf_reader as _mod
_sys.modules[__name__] = _mod
