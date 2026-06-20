# Backward compatibility adapter. New code should import from app.xninetzy.os.notes.obsidian_config
import sys as _sys
import app.xninetzy.os.notes.obsidian_config as _mod
_sys.modules[__name__] = _mod
