from dataclasses import dataclass
from typing import Callable, Optional, Dict, Any


@dataclass
class ContractFunction:
    method_name: str
    read_only: bool
    call_method: Optional[Callable] = None
    stats_method: Optional[Callable] = None
    transact_method: Optional[Callable] = None

    def call(self):
        if not self.read_only:
            raise ValueError("`call` not implemented for non-readonly method")
        return self.call_method()

    def transact(self):
        if self.read_only:
            raise ValueError("Cannot transact readonly method")
        return self.transact_method()

    def stats(
        self,
        provider: str,
        model: str,
        config: Optional[Dict[str, Any]] = None,
        plugin: Optional[str] = None,
        plugin_config: Optional[Dict[str, Any]] = None,
        runs: int = 100,
    ):
        if self.read_only:
            raise ValueError("Cannot analyze readonly method")
        return self.stats_method(provider, model, config, plugin, plugin_config, runs)
