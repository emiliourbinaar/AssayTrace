from contextlib import contextmanager
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import pytest
import io
import tarfile
from types import SimpleNamespace
import shutil
import os

from assaytrace.source import SourceContractError, acquire, unpack_archive
import assaytrace.source as source_module


@contextmanager
def local_source(payload, declared_length=None, statuses=(200,), retry_after=None):
    """Serve authored bytes on loopback; never a captured ChEMBL archive."""
    attempts = 0
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal attempts
            status = statuses[min(attempts, len(statuses) - 1)]
            attempts += 1
            if status == 0:
                self.close_connection = True
                return
            if status != 200:
                self.send_response(status)
                if retry_after is not None:
                    self.send_header("Retry-After", retry_after)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send_response(200)
            length = declared_length
            if isinstance(length, tuple):
                length = length[min(attempts - 1, len(length) - 1)]
            self.send_header("Content-Length", str(len(payload) if length is None else length))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/synthetic.bin"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_acquisition_preserves_verified_source_bytes(tmp_path):
    payload = b"authored synthetic source bytes\n"
    destination = tmp_path / "source.bin"
    with local_source(payload) as url:
        result = acquire(url, destination, sha256(payload).hexdigest())
    assert result == destination
    assert destination.read_bytes() == payload


def test_wrong_checksum_never_publishes_source(tmp_path):
    destination = tmp_path / "source.bin"
    with local_source(b"incorrect authored payload") as url:
        with pytest.raises(SourceContractError, match="checksum"):
            acquire(url, destination, "0" * 64)
    assert not destination.exists()


def test_acquisition_enforces_byte_budget_without_publishing(tmp_path):
    payload = b"x" * 20000
    destination = tmp_path / "source.bin"
    with local_source(payload) as url:
        with pytest.raises(SourceContractError, match="byte budget"):
            acquire(url, destination, sha256(payload).hexdigest(), max_bytes=10000)
    assert not destination.exists()


def test_truncated_http_body_is_rejected_even_if_payload_hash_matches(tmp_path):
    payload = b"partial authored bytes"
    destination = tmp_path / "source.bin"
    with local_source(payload, declared_length=len(payload) + 100) as url:
        with pytest.raises(SourceContractError, match="truncated"):
            acquire(url, destination, sha256(payload).hexdigest())
    assert not destination.exists()


def test_truncated_attempt_restarts_and_can_recover(tmp_path, monkeypatch):
    monkeypatch.setattr(source_module, "sleep", lambda seconds: None)
    payload = b"authored restart recovery"
    destination = tmp_path / "source.bin"
    with local_source(payload, declared_length=(len(payload) + 10, len(payload))) as url:
        try:
            result = acquire(url, destination, sha256(payload).hexdigest())
        except SourceContractError:
            result = None
    assert result == destination
    assert destination.read_bytes() == payload


def test_transient_server_error_is_retried_to_verified_completion(tmp_path):
    payload = b"authored retry success"
    destination = tmp_path / "source.bin"
    with local_source(payload, statuses=(503, 200)) as url:
        try:
            result = acquire(url, destination, sha256(payload).hexdigest())
        except OSError:
            result = None
    assert result == destination
    assert destination.read_bytes() == payload


def test_rate_limit_response_can_recover(tmp_path):
    payload = b"authored rate limit recovery"
    destination = tmp_path / "source.bin"
    with local_source(payload, statuses=(429, 200)) as url:
        try:
            result = acquire(url, destination, sha256(payload).hexdigest())
        except OSError:
            result = None
    assert result == destination
    assert destination.read_bytes() == payload


@pytest.mark.parametrize("retry_after", ["120", "Thu, 01 Jan 2099 00:00:00 GMT"])
def test_retry_after_is_honored_with_sixty_second_cap(tmp_path, monkeypatch, retry_after):
    delays = []
    monkeypatch.setattr(source_module, "sleep", delays.append)
    payload = b"authored delayed success"
    destination = tmp_path / "source.bin"
    with local_source(payload, statuses=(429, 200), retry_after=retry_after) as url:
        acquire(url, destination, sha256(payload).hexdigest())
    assert destination.read_bytes() == payload
    assert delays == [60]


def test_transient_connection_drop_is_retried(tmp_path):
    payload = b"authored connection recovery"
    destination = tmp_path / "source.bin"
    with local_source(payload, statuses=(0, 200)) as url:
        try:
            result = acquire(url, destination, sha256(payload).hexdigest())
        except OSError:
            result = None
    assert result == destination
    assert destination.read_bytes() == payload


def test_download_sync_failure_does_not_publish_source(tmp_path, monkeypatch):
    def fail_sync(descriptor):
        raise OSError("synthetic sync failure")

    monkeypatch.setattr(os, "fsync", fail_sync)
    destination = tmp_path / "source.bin"
    payload = b"authored source"
    with local_source(payload) as url:
        with pytest.raises(OSError, match="synthetic sync failure"):
            acquire(url, destination, sha256(payload).hexdigest())
    assert not destination.exists()


def test_existing_source_is_not_overwritten_by_a_different_pin(tmp_path):
    destination = tmp_path / "source.bin"
    destination.write_bytes(b"preserved original")
    before = (destination.read_bytes(), destination.stat().st_mtime_ns)
    payload = b"different source"
    with local_source(payload) as url:
        with pytest.raises(SourceContractError, match="existing"):
            acquire(url, destination, sha256(payload).hexdigest())
    assert (destination.read_bytes(), destination.stat().st_mtime_ns) == before


def test_unpack_preserves_regular_archive_bytes(tmp_path):
    archive = tmp_path / "synthetic.tar.gz"
    payload = b"authored database placeholder, not SQLite"
    with tarfile.open(archive, "w:gz") as tar:
        member = tarfile.TarInfo("release/source.db")
        member.size = len(payload)
        tar.addfile(member, io.BytesIO(payload))
    output = tmp_path / "unpacked"
    unpack_archive(archive, output)
    assert (output / "release" / "source.db").is_file()
    assert (output / "release" / "source.db").read_bytes() == payload


@pytest.mark.parametrize("name, kind", [("../escape", tarfile.REGTYPE),
    ("/absolute", tarfile.REGTYPE), ("link", tarfile.SYMTYPE),
    ("hardlink", tarfile.LNKTYPE), ("device", tarfile.CHRTYPE)])
def test_unsafe_archive_member_rejects_entire_archive_before_extraction(tmp_path, name, kind):
    archive = tmp_path / "synthetic.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        valid = tarfile.TarInfo("first.txt")
        valid.size = 1
        tar.addfile(valid, io.BytesIO(b"x"))
        member = tarfile.TarInfo(name)
        member.type = kind
        if kind in (tarfile.SYMTYPE, tarfile.LNKTYPE):
            member.linkname = "first.txt"
        tar.addfile(member)
    output = tmp_path / "unpacked"
    try:
        unpack_archive(archive, output)
    except Exception as error:
        assert isinstance(error, SourceContractError)
    else:
        pytest.fail("Unsafe archive was accepted")
    assert not output.exists()


def test_unpacked_byte_budget_is_checked_before_extraction(tmp_path):
    archive = tmp_path / "synthetic.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        member = tarfile.TarInfo("source.db")
        member.size = 20
        tar.addfile(member, io.BytesIO(b"x" * 20))
    output = tmp_path / "unpacked"
    with pytest.raises(SourceContractError, match="byte budget"):
        unpack_archive(archive, output, max_bytes=10)
    assert not output.exists()


def test_insufficient_disk_space_prevents_extraction(tmp_path, monkeypatch):
    archive = tmp_path / "synthetic.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        member = tarfile.TarInfo("source.db")
        member.size = 20
        tar.addfile(member, io.BytesIO(b"x" * 20))
    monkeypatch.setattr(shutil, "disk_usage", lambda path: SimpleNamespace(free=0))
    output = tmp_path / "unpacked"
    with pytest.raises(SourceContractError, match="disk space"):
        unpack_archive(archive, output)
    assert not output.exists()


def test_interrupted_extraction_does_not_publish_partial_source(tmp_path, monkeypatch):
    archive = tmp_path / "synthetic.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        member = tarfile.TarInfo("source.db")
        member.size = 1
        tar.addfile(member, io.BytesIO(b"x"))
    original = tarfile.TarFile.extractall

    def interrupt(tar, path, **kwargs):
        original(tar, path, **kwargs)
        raise OSError("synthetic extraction interruption")

    monkeypatch.setattr(tarfile.TarFile, "extractall", interrupt)
    output = tmp_path / "unpacked"
    with pytest.raises(OSError, match="synthetic extraction interruption"):
        unpack_archive(archive, output)
    assert not output.exists()
