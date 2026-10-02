# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
from dataclasses import dataclass
from datetime import datetime, timezone
import json


@allow_storage
@dataclass
class Watch:
    funder: Address
    finder: Address
    left_url: str
    right_url: str
    field: str
    amount: u256
    opened_at: u32
    left_value: str
    right_value: str
    status: str
    note: str


@gl.evm.contract_interface
class Payee:
    class View:
        pass

    class Write:
        pass


class SplitSignal(gl.Contract):
    watches: TreeMap[str, Watch]
    next_id: u32

    def __init__(self):
        self.next_id = u32(1)

    def _now(self) -> int:
        return int(datetime.now(timezone.utc).timestamp())

    def _pay(self, to: Address, amount: u256) -> None:
        Payee(to).emit_transfer(value=amount)

    def _read(self, url: str, field: str) -> str:
        try:
            page = gl.nondet.web.render(url, mode="html")
            text = page.lower() if page else ""
            if not text:
                return json.dumps({"ok": "no", "value": ""}, sort_keys=True)
            return json.dumps(
                {"ok": "yes", "value": "yes" if field in text else "no"},
                sort_keys=True,
            )
        except Exception:
            return json.dumps({"ok": "no", "value": ""}, sort_keys=True)

    @gl.public.write.payable
    def open_watch(self, left_url: str, right_url: str, field: str) -> None:
        left = left_url.strip()
        right = right_url.strip()
        key = field.strip().lower()
        if not left or not right or left == right:
            raise Exception("two different urls required")
        if len(key) < 3 or len(key) > 32:
            raise Exception("field must be 3-32 chars")
        if int(gl.message.value) <= 0:
            raise Exception("lock GEN")
        cid = int(self.next_id)
        self.next_id = u32(cid + 1)
        self.watches[str(cid)] = Watch(
            funder=gl.message.sender_address,
            finder=Address("0x0000000000000000000000000000000000000000"),
            left_url=left,
            right_url=right,
            field=key,
            amount=gl.message.value,
            opened_at=u32(self._now()),
            left_value="",
            right_value="",
            status="OPEN",
            note="funded",
        )

    @gl.public.write
    def recheck(self, watch_id: str) -> None:
        rec = self.watches[watch_id]
        if rec.status != "OPEN":
            raise Exception("not open")
        left_url = rec.left_url
        right_url = rec.right_url
        field = rec.field

        def both() -> str:
            return json.dumps(
                {
                    "left": json.loads(self._read(left_url, field)),
                    "right": json.loads(self._read(right_url, field)),
                },
                sort_keys=True,
            )

        raw = gl.eq_principle.strict_eq(both)
        try:
            parsed = raw if isinstance(raw, dict) else json.loads(str(raw))
        except Exception:
            parsed = {}
        left = parsed.get("left", {})
        right = parsed.get("right", {})
        if left.get("ok") != "yes" or right.get("ok") != "yes":
            rec.note = "a page is unreadable"
            self.watches[watch_id] = rec
            return
        rec.left_value = str(left.get("value"))
        rec.right_value = str(right.get("value"))
        if rec.left_value == rec.right_value:
            rec.status = "AGREED"
            rec.note = "sources still match"
            self.watches[watch_id] = rec
            return
        amt = rec.amount
        rec.status = "SPLIT"
        rec.finder = gl.message.sender_address
        rec.note = "sources diverged"
        self.watches[watch_id] = rec
        self._pay(gl.message.sender_address, amt)

    @gl.public.write
    def refund(self, watch_id: str) -> None:
        rec = self.watches[watch_id]
        if rec.status != "OPEN":
            raise Exception("not open")
        if self._now() < int(rec.opened_at) + 3600:
            raise Exception("wait an hour")
        amt = rec.amount
        rec.status = "REFUNDED"
        rec.note = "funder exit"
        self.watches[watch_id] = rec
        self._pay(rec.funder, amt)

    @gl.public.view
    def get_watch(self, watch_id: str) -> str:
        if watch_id not in self.watches:
            return "{}"
        rec = self.watches[watch_id]
        return json.dumps(
            {
                "funder": str(rec.funder),
                "finder": str(rec.finder),
                "left_url": rec.left_url,
                "right_url": rec.right_url,
                "field": rec.field,
                "amount": str(int(rec.amount)),
                "opened_at": int(rec.opened_at),
                "left_value": rec.left_value,
                "right_value": rec.right_value,
                "status": rec.status,
                "note": rec.note,
            }
        )
