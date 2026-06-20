# Backward compatibility adapter. New code should import from app.xninetzy.os.academic.hebat.course_extractor
import sys as _sys
import app.xninetzy.os.academic.hebat.course_extractor as _mod
_sys.modules[__name__] = _mod
