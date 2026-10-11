import importlib.util
import sys
import types
from pathlib import Path

import pytest


CONTRACT_PATH = Path(__file__).parents[1] / "contracts" / "SplitSignal.py"
BOND = 10**18
ALICE = "0x1111111111111111111111111111111111111111"
BOB = "0x2222222222222222222222222222222222222222"
FEE_TO = "0x3333333333333333333333333333333333333333"


class Address(str):
    pass


class u256(int):
    pass


class u32(int):
    pass


class TreeMap(dict):
    pass


def allow_storage(cls):
    return cls


class Contract:
    pass


class WriteDecorator:
    def __call__(self, fn):
        return fn

    def payable(self, fn):
        return fn


class Public:
    write = WriteDecorator()

    @staticmethod
    def view(fn):
        return fn


class Evm:
    @staticmethod
    def contract_interface(cls):
        return cls


class StrictEq:
    @staticmethod
    def strict_eq(fn):
        return fn()


class EqPrinciple:
    strict_eq = StrictEq.strict_eq


class FakeWeb:
    def __init__(self):
        self.pages = {}

    def render(self, url, mode="html"):
        assert mode == "html"
        return self.pages[url]


class FakePayee:
    transfers = []

    def __init__(self, to):
        self.to = Address(to)

    def emit_transfer(self, value):
        self.transfers.append((str(self.to), int(value)))


def load_contract_module():
    web = FakeWeb()
    message = types.SimpleNamespace(
        sender_address=Address(FEE_TO),
        value=u256(0),
    )

    gl = types.ModuleType("genlayer")
    gl.contract = types.SimpleNamespace(Contract=Contract)
    gl.public = Public()
    gl.evm = Evm()
    gl.eq_principle = EqPrinciple()
    gl.nondet = types.SimpleNamespace(web=web)
    gl.message = message

    types_mod = types.ModuleType("genlayer.types")
    types_mod.Address = Address
    types_mod.u256 = u256
    types_mod.u32 = u32
    types_mod.TreeMap = TreeMap
    types_mod.allow_storage = allow_storage
    types_mod.__all__ = [
        "Address",
        "u256",
        "u32",
        "TreeMap",
        "allow_storage",
    ]

    previous_genlayer = sys.modules.get("genlayer")
    previous_types = sys.modules.get("genlayer.types")
    sys.modules["genlayer"] = gl
    sys.modules["genlayer.types"] = types_mod

    try:
        spec = importlib.util.spec_from_file_location(
            "splitsignal_contract_security_test",
            CONTRACT_PATH,
        )
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
    finally:
        if previous_genlayer is None:
            sys.modules.pop("genlayer", None)
        else:
            sys.modules["genlayer"] = previous_genlayer
        if previous_types is None:
            sys.modules.pop("genlayer.types", None)
        else:
            sys.modules["genlayer.types"] = previous_types

    module.Payee = FakePayee
    module.gl = gl
    return module, web, message


def new_contract(module):
    contract = module.SplitSignal()
    contract.watches = TreeMap()
    contract.split_commitments = TreeMap()
    contract.split_commit_times = TreeMap()
    return contract


def test_copied_or_front_run_reveal_cannot_redirect_discoverer_reward():
    module, web, message = load_contract_module()
    FakePayee.transfers = []

    now = [1_800_000_000]
    contract = new_contract(module)
    contract._now = lambda: now[0]

    left = "https://left.test/source"
    right = "https://right.test/source"
    web.pages[left] = "<p>iana</p>"
    web.pages[right] = "<p>iana</p>"

    message.sender_address = Address(ALICE)
    message.value = u256(BOND)
    contract.open_watch(left, right, "iana", "1")

    # The public sources diverge after the Watch has opened.
    web.pages[right] = "<p>changed</p>"
    salt = "alice-private-discovery"
    alice_commitment = contract._claim_digest(
        "1",
        Address(ALICE),
        salt,
    )

    # Alice reports first.
    message.sender_address = Address(ALICE)
    message.value = u256(0)
    contract.commit_split("1", alice_commitment)

    # Bob can see and even copy Alice's commitment into Bob's own reporter slot.
    # That still must not let Bob redirect the payout to himself.
    message.sender_address = Address(BOB)
    contract.commit_split("1", alice_commitment)

    now[0] += module.MIN_COMMIT_AGE + 1

    with pytest.raises(Exception, match="split commitment mismatch"):
        contract.recheck("1", Address(BOB), salt)

    # If Bob front-runs the copied reveal byte-for-byte, the committed
    # recipient is still Alice, so the reward cannot be stolen.
    contract.recheck("1", Address(ALICE), salt)

    watch = contract.watches["1"]
    assert watch.status == "SPLIT"
    assert str(watch.finder).lower() == ALICE.lower()

    finder_reward = BOND - (BOND * module.FEE_BPS // 10_000)
    protocol_fee = BOND * module.FEE_BPS // 10_000

    assert FakePayee.transfers == [
        (ALICE, finder_reward),
        (FEE_TO, protocol_fee),
    ]


def test_commitment_is_bound_to_watch_and_recipient():
    module, _, _ = load_contract_module()
    contract = new_contract(module)

    salt = "same-secret"
    alice_watch_1 = contract._claim_digest("1", Address(ALICE), salt)
    alice_watch_2 = contract._claim_digest("2", Address(ALICE), salt)
    bob_watch_1 = contract._claim_digest("1", Address(BOB), salt)

    assert alice_watch_1 != alice_watch_2
    assert alice_watch_1 != bob_watch_1
