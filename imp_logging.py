# openedx/core/lib/imp_logging.py

import os
from datetime import datetime

LOG_FILE = "/home/openedx/.local/share/tutor/imp_logging.log"

def append_log(message: str):
    """
    Appenduje poruku u imp_logging.log sa timestamp-om.
    Ako direktorijum/fajl ne postoji, biće kreiran.
    """
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.utcnow().isoformat()}] {message}\n")
