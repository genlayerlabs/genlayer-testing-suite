"""Regression tests for the stdin-injection temp file lifecycle.

See issue #99 (bug 3): unlinking the temp file used to inject the message
context into fd 0 immediately after os.dup2() works on POSIX (the directory
entry is removed but the data stays available via the still-open fd) but
raises PermissionError on Windows, which locks files with open handles.

The fix defers the unlink until fd 0's duplicate has actually been closed
in VMContext._cleanup_after_deactivate.
"""

import os

import pytest

from gltest.direct import loader
from gltest.direct.vm import VMContext


class _FakeAddress:
    def __init__(self, data):
        self.data = data


class _FakeCalldata:
    """Minimal calldata stand-in: encode() just needs to produce bytes."""

    @staticmethod
    def encode(_message_data):
        return b"fake-encoded-message"


@pytest.fixture
def fake_sdk(monkeypatch):
    """Avoid requiring a real downloaded SDK for this unit test."""
    monkeypatch.setattr(loader, "import_calldata", lambda: _FakeCalldata())
    monkeypatch.setattr(loader, "import_address", lambda: _FakeAddress)


class TestInjectMessageToFd0:
    def test_temp_file_is_not_deleted_immediately(self, fake_sdk):
        """Regression: the temp file must still exist right after
        _inject_message_to_fd0 returns, because fd 0 still references it.
        Deleting it immediately is what breaks on Windows."""
        vm = VMContext()
        original_stdin = os.dup(0)
        try:
            loader._inject_message_to_fd0(vm)

            temp_path = getattr(vm, "_stdin_temp_path", None)
            assert temp_path is not None, "temp path must be recorded on vm for deferred cleanup"
            assert os.path.exists(temp_path), "temp file must not be unlinked while fd 0 still holds it open"
        finally:
            # Restore real stdin and clean up manually (mirrors _cleanup_after_deactivate)
            os.dup2(original_stdin, 0)
            os.close(original_stdin)
            stdin_fd = getattr(vm, "_original_stdin_fd", None)
            if stdin_fd is not None:
                os.close(stdin_fd)
            temp_path = getattr(vm, "_stdin_temp_path", None)
            if temp_path is not None:
                os.unlink(temp_path)

    def test_cleanup_after_deactivate_removes_temp_file(self, fake_sdk):
        """After the VM context restores stdin, the deferred temp file
        must be cleaned up (and cleanup must not raise, mirroring the
        try/except OSError guard needed for Windows)."""
        vm = VMContext()
        original_stdin = os.dup(0)
        try:
            loader._inject_message_to_fd0(vm)
            temp_path = vm._stdin_temp_path
            assert os.path.exists(temp_path)

            vm._cleanup_after_deactivate()

            assert not os.path.exists(temp_path), "temp file must be removed after cleanup"
            assert vm._stdin_temp_path is None
            assert vm._original_stdin_fd is None
        finally:
            os.dup2(original_stdin, 0)
            os.close(original_stdin)

    def test_cleanup_is_safe_when_nothing_was_injected(self):
        """Calling cleanup on a VM that never replaced stdin (e.g. ImportError
        early-return in _inject_message_to_fd0) must not raise."""
        vm = VMContext()
        vm._cleanup_after_deactivate()  # should not raise

    def test_cleanup_tolerates_missing_temp_file(self, fake_sdk):
        """If the temp file was already removed some other way, cleanup
        must swallow the OSError instead of propagating it (same guard
        already used for the stdin dup2/close above it)."""
        vm = VMContext()
        original_stdin = os.dup(0)
        try:
            loader._inject_message_to_fd0(vm)
            # Restore fd 0 before manually unlinking below — otherwise this
            # unlink is exactly the "unlink while fd 0 still references the
            # file" case this whole fix exists to avoid, and would itself
            # raise PermissionError on Windows. vm._original_stdin_fd is
            # left as-is so _cleanup_after_deactivate's own restore path is
            # still exercised below (redundant dup2 onto the same target,
            # then close — harmless).
            os.dup2(original_stdin, 0)
            os.unlink(vm._stdin_temp_path)  # simulate external removal

            vm._cleanup_after_deactivate()  # should not raise despite missing file

            assert vm._stdin_temp_path is None
        finally:
            os.dup2(original_stdin, 0)
            os.close(original_stdin)
