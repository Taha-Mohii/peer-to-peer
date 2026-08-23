import hashlib


def get_checksum(filepath: str) -> str:
    """Returns MD5 hash of a file as a hex string."""
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(4096):
            md5.update(chunk)
    return md5.hexdigest()
