from urllib.request import urlopen
from hashlib import sha256
from urllib.error import HTTPError, URLError
from time import sleep
import tarfile
import shutil
import os
from pathlib import Path, PurePosixPath
from tempfile import mkdtemp
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone


class SourceContractError(ValueError):
    pass


class TruncatedTransfer(SourceContractError):
    pass


def unpack_archive(archive, output, *, max_bytes=80 * 1024**3):
    with tarfile.open(archive, "r:gz") as tar:
        members = tar.getmembers()
        if sum(member.size for member in members) > max_bytes:
            raise SourceContractError("Unpacked source exceeds byte budget")
        if shutil.disk_usage(output.parent).free < sum(member.size for member in members) + 1024**3:
            raise SourceContractError("Insufficient disk space for unpacked source and reserve")
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or not (member.isfile() or member.isdir()):
                raise SourceContractError(f"Unsafe archive member: {member.name}")
        stage = Path(mkdtemp(prefix=".unpack-", dir=output.parent))
        tar.extractall(stage, members=members, filter="data")
        stage.rename(output)


def acquire(url, destination, expected_sha256, *, max_bytes=8 * 1024**3):
    if destination.exists():
        digest = sha256()
        with destination.open("rb") as stream:
            while chunk := stream.read(1024**2):
                digest.update(chunk)
        if digest.hexdigest() != expected_sha256:
            raise SourceContractError("existing source disagrees with checksum")
        return destination
    for attempt in range(3):
        try:
            return _acquire_once(url, destination, expected_sha256, max_bytes)
        except HTTPError as error:
            if (error.code != 429 and not 500 <= error.code <= 599) or attempt == 2:
                raise
            delay = 2**attempt
            retry_after = error.headers.get("Retry-After")
            if retry_after is not None:
                try:
                    delay = int(retry_after)
                except ValueError:
                    delay = (parsedate_to_datetime(retry_after) - datetime.now(timezone.utc)).total_seconds()
            sleep(min(60, max(0, delay)))
        except (URLError, ConnectionError, TimeoutError, TruncatedTransfer):
            if attempt == 2:
                raise
            sleep(2**attempt)


def _acquire_once(url, destination, expected_sha256, max_bytes):
    partial = destination.with_name(destination.name + ".part")
    digest = sha256()
    total = 0
    with urlopen(url, timeout=30) as response, partial.open("wb") as stream:
        while chunk := response.read(min(1024**2, max_bytes - total + 1)):
            total += len(chunk)
            if total > max_bytes:
                raise SourceContractError("Source exceeds byte budget")
            digest.update(chunk)
            stream.write(chunk)
        declared_length = response.headers.get("Content-Length")
        if declared_length is not None and total != int(declared_length):
            raise TruncatedTransfer("Source response truncated")
        stream.flush()
        os.fsync(stream.fileno())
    if digest.hexdigest() != expected_sha256:
        raise SourceContractError("Source checksum mismatch")
    partial.rename(destination)
    return destination
