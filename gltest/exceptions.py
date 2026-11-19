import base64
import binascii
import json
from typing import Any, Dict, Optional

from genlayer_py.exceptions import GenLayerError


class DeploymentError(Exception):
    """Raised when a contract deployment fails."""

    pass


class FixtureSnapshotError(Exception):
    """Raised when there's an error restoring a snapshot."""

    pass


class FixtureAnonymousFunctionError(Exception):
    """Raised when a fixture is an anonymous function."""

    pass


class InvalidSnapshotError(Exception):
    """Raised when a snapshot is invalid."""

    pass


class HelperError(Exception):
    """Raised when a helper function fails."""

    pass


_STDERR_TAIL_CHARS = 4000
_DATA_PREVIEW_CHARS = 1000


class GenLayerRPCError(GenLayerError):
    """Raised when a GenLayer JSON-RPC call returns an error.

    Unlike the SDK's plain ``GenLayerError``, this keeps the JSON-RPC
    ``error.data`` payload. For failed ``gen_call``/``sim_call`` executions
    Studio puts the leader receipt there, so the GenVM stderr (the contract
    traceback) and the execution error are shown in the message and exposed
    as attributes.
    """

    def __init__(self, method: str, code: Any, message: str, data: Any = None):
        self.method = method
        self.code = code
        self.rpc_message = message
        self.data = data
        super().__init__(self._format())

    @property
    def receipt(self) -> Optional[Dict[str, Any]]:
        receipt = self.data.get("receipt") if isinstance(self.data, dict) else None
        return receipt if isinstance(receipt, dict) else None

    @property
    def genvm_result(self) -> Dict[str, Any]:
        genvm_result = (self.receipt or {}).get("genvm_result")
        return genvm_result if isinstance(genvm_result, dict) else {}

    @property
    def stderr(self) -> Optional[str]:
        return self.genvm_result.get("stderr") or None

    @property
    def stdout(self) -> Optional[str]:
        return self.genvm_result.get("stdout") or None

    @property
    def execution_error(self) -> Optional[str]:
        """Best-effort description of why the contract execution failed."""
        genvm_result = self.genvm_result
        for key in ("error_description", "raw_error"):
            value = genvm_result.get(key)
            if value:
                return value if isinstance(value, str) else json.dumps(value)
        result = (self.receipt or {}).get("result")
        if isinstance(result, str) and result:
            try:
                raw = base64.b64decode(result, validate=True)
            except (binascii.Error, ValueError):
                return None
            # First byte is the GenVM result code; the rest is the message.
            text = raw[1:].decode("utf-8", errors="replace").strip()
            return text or None
        return None

    def _format(self) -> str:
        lines = [f"{self.method} failed (code={self.code}): {self.rpc_message}"]
        if self.receipt is not None:
            execution_result = self.receipt.get("execution_result")
            if execution_result:
                lines.append(f"execution_result: {execution_result}")
            execution_error = self.execution_error
            if execution_error:
                lines.append(f"error: {execution_error}")
            stderr = self.stderr
            if stderr:
                if len(stderr) > _STDERR_TAIL_CHARS:
                    stderr = "...(truncated)\n" + stderr[-_STDERR_TAIL_CHARS:]
                lines.append("stderr:\n" + stderr.rstrip())
        elif self.data not in (None, {}, [], ""):
            try:
                preview = json.dumps(self.data, default=str)
            except (TypeError, ValueError):
                preview = repr(self.data)
            if len(preview) > _DATA_PREVIEW_CHARS:
                preview = preview[:_DATA_PREVIEW_CHARS] + "...(truncated)"
            lines.append(f"data: {preview}")
        return "\n".join(lines)
