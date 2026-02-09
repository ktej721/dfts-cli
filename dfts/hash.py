import hashlib

def sha256_file(path: str) -> str:
    """
    calculates the sha-256 hash of a file.

    args:
        path: path to the file to be hashed.

    returns:
        the hexadecimal digest of the file's hash.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
