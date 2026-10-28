import hashlib
import json
import os
import tempfile
from pathlib import Path


def atomic_bytes(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)
    return hashlib.sha256(data).hexdigest()


def atomic_json(path, obj):
    return atomic_bytes(path, (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
