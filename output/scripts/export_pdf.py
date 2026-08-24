"""Export the revised DOCX to PDF via LibreOffice UNO, updating the TOC first.

Run:  python scripts/export_pdf.py
Output: ../Tugas_Data_Exploration_SID303_187241037_Revised.pdf
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

import uno
from com.sun.star.beans import PropertyValue

BASE = Path(__file__).resolve().parent.parent
DOCX = BASE / "Tugas_Data_Exploration_SID303_187241037_Revised.docx"
PDF = BASE / "Tugas_Data_Exploration_SID303_187241037_Revised.pdf"

PORT = 2002


def start_soffice():
    subprocess.Popen(
        [
            "soffice", "--headless", "--invisible", "--norestore", "--nologo",
            f"--accept=socket,host=127.0.0.1,port={PORT};urp;",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def connect(timeout: int = 60):
    local_context = uno.getComponentContext()
    resolver = local_context.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local_context
    )
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            return resolver.resolve(
                f"uno:socket,host=127.0.0.1,port={PORT};urp;StarOffice.ComponentContext"
            )
        except Exception:
            time.sleep(1)
    raise RuntimeError("cannot connect to LibreOffice UNO")


def prop(name: str, value) -> PropertyValue:
    p = PropertyValue()
    p.Name = name
    p.Value = value
    return p


def main():
    start_soffice()
    ctx = connect()
    smgr = ctx.ServiceManager
    desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)

    doc = desktop.loadComponentFromURL(
        DOCX.as_uri(), "_blank", 0, (prop("Hidden", True),)
    )

    indexes = doc.getDocumentIndexes()
    for i in range(indexes.getCount()):
        indexes.getByIndex(i).update()

    doc.storeToURL(PDF.as_uri(), (prop("FilterName", "writer_pdf_Export"),))
    doc.close(False)
    print(f"wrote {PDF}")


if __name__ == "__main__":
    main()