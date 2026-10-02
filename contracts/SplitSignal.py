# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
from dataclasses import dataclass
from datetime import datetime, timezone
import json

FEE_BPS = 500
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
    shares: TreeMap[str, u256]
    next_id: u32
    pool: u256
    reserved: u256
    share_supply: u256

    def __init__(self):
        self.next_id = u32(1)
        self.pool = u256(0)
        self.reserved = u256(0)
        self.share_supply = u256(0)

    def _now(self) -> int:
        return int(datetime.now(timezone.utc).timestamp())

    def _pay(self, to: Address, amount: u256) -> None:
        if int(amount) > 0:
            Payee(to).emit_transfer(value=amount)

    def _key(self, who: Address) -> str:
        return str(who).lower()

    def _held(self, who: Address) -> int:
        k = self._key(who)
        return int(self.shares[k]) if k in self.shares else 0

    def _balance(self, who: Address) -> int:
        if self._held(who) == 0 or int(self.share_supply) == 0 or int(self.pool) == 0:
            return 0
        return self._held(who) * int(self.pool) // int(self.share_supply)

    def _free(self) -> int:
        return int(self.pool) - int(self.reserved)

    def _credit(self, who: Address, amount: int) -> None:
        if amount <= 0:
            raise Exception("send GEN")
        supply = int(self.share_supply)
        pool = int(self.pool)
        minted = amount if supply == 0 or pool == 0 else amount * supply // pool
        if minted <= 0:
            raise Exception("share dust")
        self.shares[self._key(who)] = u256(self._held(who) + minted)
        self.share_supply = u256(supply + minted)
        self.pool = u256(pool + amount)

    def _take(self, who: Address, amount: int) -> None:
        if amount <= 0 or amount > self._balance(who) or amount > self._free():
            raise Exception("insufficient free balance")
        supply = int(self.share_supply)
        burned = amount * supply // int(self.pool)
        if burned <= 0 or burned > self._held(who):
            raise Exception("share dust")
        self.shares[self._key(who)] = u256(self._held(who) - burned)
        self.share_supply = u256(supply - burned)
        self.pool = u256(int(self.pool) - amount)

    def _https(self, url: str) -> str:
        if not url.startswith("https://") or " " in url:
            raise Exception("https url required")
        return url

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
    def deposit(self) -> None:
        self._credit(gl.message.sender_address, int(gl.message.value))

    @gl.public.write
    def withdraw(self, amount: str) -> None:
        amt = int(amount)
        who = gl.message.sender_address
        self._take(who, amt)
        self._pay(who, u256(amt))

    @gl.public.write.payable
    def open_watch(self, left_url: str, right_url: str, field: str, hours: str, amount: str) -> None:
        if int(gl.message.value) > 0:
            self._credit(gl.message.sender_address, int(gl.message.value))
        left = self._https(left_url.strip())
        right = self._https(right_url.strip())
        key = field.strip().lower()
        window = int(hours)
        bond = int(amount)
        if left == right:
            raise Exception("two different urls required")
        if len(key) < 3 or len(key) > 32:
            raise Exception("field must be 3-32 chars")
        if window < 1 or window > 168:
            raise Exception("window must be 1-168 hours")
        if bond <= 0:
            raise Exception("lock GEN")
        parsed = self._both(left, right, key)
        lv = parsed.get("left", {})
        rv = parsed.get("right", {})
        if lv.get("ok") != "yes" or rv.get("ok") != "yes":
            raise Exception("a page is unreadable")
        if str(lv.get("value")) != str(rv.get("value")):
            raise Exception("already split")
        who = gl.message.sender_address
        self._take(who, bond)
        self.reserved = u256(int(self.reserved) + bond)
        cid = int(self.next_id)
        self.next_id = u32(cid + 1)
        now = self._now()
        self.watches[str(cid)] = Watch(
            funder=who, finder=ZERO, left_url=left, right_url=right, field=key,
            amount=u256(bond), opened_at=u32(now), deadline=u32(now + window * 3600),
            left_value=str(lv.get("value")), right_value=str(rv.get("value")),
            status="OPEN", note="sources matched at open",
        )

    @gl.public.write
    def recheck(self, watch_id: str) -> None:
        rec = self.watches[watch_id]
        if rec.status != "OPEN":
            raise Exception("not open")
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
        self.reserved = u256(int(self.reserved) - gross)
        self.pool = u256(int(self.pool) + fee)
        rec.status = "SPLIT"
        rec.finder = gl.message.sender_address
        rec.note = "sources diverged"
        self.watches[watch_id] = rec
        self._pay(gl.message.sender_address, u256(gross - fee))

    @gl.public.write
    def refund(self, watch_id: str) -> None:
        rec = self.watches[watch_id]
        if rec.status != "OPEN":
            raise Exception("not open")
        if self._now() < int(rec.deadline):
            raise Exception("wait for the window")
        amt = int(rec.amount)
        self.reserved = u256(int(self.reserved) - amt)
        rec.status = "REFUNDED"
        rec.note = "funder exit"
        self.watches[watch_id] = rec
        self._credit(rec.funder, amt)

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
    def get_pool(self) -> str:
        return json.dumps({
            "pool": str(int(self.pool)), "reserved": str(int(self.reserved)),
            "free": str(self._free()), "share_supply": str(int(self.share_supply)),
            "next_id": str(int(self.next_id)), "fee_bps": "500",
        })

    @gl.public.view
    def get_share(self, who: str) -> str:
        addr = Address(who)
        return json.dumps({"account": who, "shares": str(self._held(addr)), "balance": str(self._balance(addr))})

    @gl.public.view
    def next_watch(self) -> str:
        return str(int(self.next_id))
