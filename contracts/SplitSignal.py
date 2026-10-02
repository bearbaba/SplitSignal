# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
from dataclasses import dataclass
from datetime import datetime, timezone
import json

FEE_BPS = 500
MIN_BOND = 10**16
ZERO = Address("0x0000000000000000000000000000000000000000")

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
    deadline: u32
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
    fee_to: Address

    def __init__(self):
        self.next_id = u32(1)
        self.fee_to = gl.message.sender_address

    def _now(self) -> int:
        return int(datetime.now(timezone.utc).timestamp())

    def _pay(self, to: Address, amount: int) -> None:
        if amount > 0:
            Payee(to).emit_transfer(value=u256(amount))

    def _https(self, url: str) -> str:
        raw = url.strip()
        if not raw.startswith("https://") or " " in raw:
            raise Exception("https url required")
        body = raw[8:]
        body = body.split("#", 1)[0]
        if body.endswith("/"):
            body = body[:-1]
        host, _, rest = body.partition("/")
        out = "https://" + host.lower()
        if rest:
            out += "/" + rest
        return out

    def _hit(self, text: str, field: str) -> str:
        return "yes" if (" " + field + " ") in (" " + text.replace("<", " ").replace(">", " ") + " ") else "no"

    def _read(self, url: str, field: str) -> str:
        try:
            page = gl.nondet.web.render(url, mode="html")
            text = page.lower() if page else ""
            if not text:
                return json.dumps({"ok": "no", "value": ""}, sort_keys=True)
            return json.dumps({"ok": "yes", "value": self._hit(text, field)}, sort_keys=True)
        except Exception:
            return json.dumps({"ok": "no", "value": ""}, sort_keys=True)

    def _both(self, left_url: str, right_url: str, field: str) -> dict:
        def run() -> str:
            return json.dumps(
                {"left": json.loads(self._read(left_url, field)), "right": json.loads(self._read(right_url, field))},
                sort_keys=True,
            )
        raw = gl.eq_principle.strict_eq(run)
        try:
            return raw if isinstance(raw, dict) else json.loads(str(raw))
        except Exception:
            return {}

    @gl.public.write.payable
    def open_watch(self, left_url: str, right_url: str, field: str, hours: str) -> None:
        left = self._https(left_url)
        right = self._https(right_url)
        key = field.strip().lower()
        window = int(hours)
        bond = int(gl.message.value)
        if left == right:
            raise Exception("two different urls required")
        if len(key) < 3 or len(key) > 32:
            raise Exception("field must be 3-32 chars")
        if window < 1 or window > 168:
            raise Exception("window must be 1-168 hours")
        if bond < MIN_BOND:
            raise Exception("bond below minimum")
        parsed = self._both(left, right, key)
        lv = parsed.get("left", {})
        rv = parsed.get("right", {})
        if lv.get("ok") != "yes" or rv.get("ok") != "yes":
            raise Exception("a page is unreadable")
        if str(lv.get("value")) != str(rv.get("value")):
            raise Exception("already split")
        cid = int(self.next_id)
        self.next_id = u32(cid + 1)
        now = self._now()
        self.watches[str(cid)] = Watch(
            funder=gl.message.sender_address, finder=ZERO, left_url=left, right_url=right, field=key,
            amount=u256(bond), opened_at=u32(now), deadline=u32(now + window * 3600),
            left_value=str(lv.get("value")), right_value=str(rv.get("value")),
            status="OPEN", note="sources matched at open",
        )

    @gl.public.write
    def recheck(self, watch_id: str) -> None:
        rec = self.watches[watch_id]
        if rec.status != "OPEN":
            raise Exception("not open")
        if self._now() >= int(rec.deadline):
            raise Exception("window closed")
        parsed = self._both(rec.left_url, rec.right_url, rec.field)
        left = parsed.get("left", {})
        right = parsed.get("right", {})
        if left.get("ok") != "yes" or right.get("ok") != "yes":
            rec.note = "a page is unreadable"
            self.watches[watch_id] = rec
            return
        rec.left_value = str(left.get("value"))
        rec.right_value = str(right.get("value"))
        if rec.left_value == rec.right_value:
            rec.note = "sources still match"
            self.watches[watch_id] = rec
            return
        gross = int(rec.amount)
        fee = gross * FEE_BPS // 10000
        rec.status = "SPLIT"
        rec.finder = gl.message.sender_address
        rec.note = "sources diverged"
        self.watches[watch_id] = rec
        self._pay(gl.message.sender_address, gross - fee)
        self._pay(self.fee_to, fee)

    @gl.public.write
    def refund(self, watch_id: str) -> None:
        rec = self.watches[watch_id]
        if rec.status != "OPEN":
            raise Exception("not open")
        if self._now() < int(rec.deadline):
            raise Exception("wait for the window")
        amt = int(rec.amount)
        rec.status = "REFUNDED"
        rec.note = "funder exit"
        self.watches[watch_id] = rec
        self._pay(rec.funder, amt)

    @gl.public.view
    def get_watch(self, watch_id: str) -> str:
        if watch_id not in self.watches:
            return "{}"
        rec = self.watches[watch_id]
        return json.dumps({
            "id": watch_id, "funder": str(rec.funder), "finder": str(rec.finder),
            "left_url": rec.left_url, "right_url": rec.right_url, "field": rec.field,
            "amount": str(int(rec.amount)), "opened_at": int(rec.opened_at),
            "deadline": int(rec.deadline), "left_value": rec.left_value,
            "right_value": rec.right_value, "status": rec.status, "note": rec.note,
        })

    @gl.public.view
    def next_watch(self) -> str:
        return str(int(self.next_id))
