# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *


class LegacyStorage(gl.Contract):
    label: str
    notes: TreeMap[Address, str]

    def __init__(self, label: str):
        self.label = label

    @gl.public.view
    def get_label(self) -> str:
        return self.label

    @gl.public.view
    def get_note(self, account: str) -> str:
        return self.notes.get(Address(account), "")

    @gl.public.write
    def set_note(self, note: str) -> None:
        self.notes[gl.message.sender_address] = note

    @gl.public.write
    def fetch_label(self, url: str) -> None:
        def leader() -> str:
            return gl.nondet.web.render(url, mode="text")

        self.label = gl.eq_principle.strict_eq(leader)

    @gl.public.write
    def fetch_checked(self, url: str) -> None:
        def leader() -> str:
            return gl.nondet.web.render(url, mode="text")

        def validator(result) -> bool:
            return isinstance(result, gl.vm.Return) and result.calldata == "rendered"

        self.label = gl.vm.run_nondet(leader, validator)

    @gl.public.write
    def fail(self, reason: str) -> None:
        raise gl.vm.UserError(reason)
