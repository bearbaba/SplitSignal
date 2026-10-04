import json

LEFT = "https://left.test/a"
RIGHT = "https://right.test/b"
BOND = 10**18


def deploy(direct_deploy):
    return direct_deploy("contracts/SplitSignal.py")


def mock_pages(direct_vm, left, right):
    direct_vm.mock_web(r"https://left\.test", {"status": 200, "body": left})
    direct_vm.mock_web(r"https://right\.test", {"status": 200, "body": right})


def watch(contract, watch_id="1"):
    return json.loads(contract.get_watch(watch_id))


def test_rejects_same_url_and_short_field(direct_vm, direct_deploy):
    direct_vm.value = BOND
    c = deploy(direct_deploy)

    with direct_vm.expect_revert("two different urls required"):
        c.open_watch(LEFT, LEFT, "iana", "1")

    with direct_vm.expect_revert("field must be 3-32 chars"):
        c.open_watch(LEFT, RIGHT, "id", "1")


def test_split_pays_caller_once(direct_vm, direct_deploy, direct_alice):
    mock_pages(
        direct_vm,
        "<p>iana keeps this zone</p>",
        "<p>iana is also here</p>",
    )
    direct_vm.value = BOND
    c = deploy(direct_deploy)

    with direct_vm.prank(direct_alice):
        c.open_watch(LEFT, RIGHT, "iana", "1")

        direct_vm.clear_mocks()
        direct_vm.mock_web(
            r"https://left\.test",
            {"status": 200, "body": "<p>iana keeps this zone</p>"},
        )
        direct_vm.mock_web(
            r"https://right\.test",
            {"status": 200, "body": "<p>no token here</p>"},
        )
        c.recheck("1")

    rec = watch(c)
    assert rec["status"] == "SPLIT"
    assert rec["left_value"] == "yes"
    assert rec["right_value"] == "no"
    assert rec["finder"].lower() == "0x" + direct_alice.hex().lower()


def test_agreed_stays_open_and_does_not_pay(
    direct_vm, direct_deploy
):
    mock_pages(direct_vm, "iana", "the iana record")
    direct_vm.value = BOND
    c = deploy(direct_deploy)

    c.open_watch(LEFT, RIGHT, "iana", "1")
    c.recheck("1")

    rec = watch(c)
    assert rec["status"] == "OPEN"
    assert rec["left_value"] == "yes"
    assert rec["right_value"] == "yes"
    assert rec["note"] == "sources still match"


def test_unreadable_page_is_rejected_at_open(
    direct_vm, direct_deploy
):
    direct_vm.mock_web(
        r"https://left\.test",
        {"status": 500, "body": ""},
    )
    direct_vm.mock_web(
        r"https://right\.test",
        {"status": 200, "body": "iana"},
    )

    direct_vm.value = BOND
    c = deploy(direct_deploy)

    with direct_vm.expect_revert("a page is unreadable"):
        c.open_watch(LEFT, RIGHT, "iana", "1")


def test_short_window_and_bond_are_rejected(
    direct_vm, direct_deploy
):
    direct_vm.value = BOND

    c = deploy(direct_deploy)

    with direct_vm.expect_revert("window must be 1-168 hours"):
        c.open_watch(LEFT, RIGHT, "iana", "0")

    direct_vm.value = 0
    with direct_vm.expect_revert("bond below minimum"):
        c.open_watch(LEFT, RIGHT, "iana", "1")


def test_urls_are_normalized_and_field_is_lowercased(
    direct_vm, direct_deploy
):
    mock_pages(direct_vm, "IANA", "iana")
    direct_vm.value = BOND
    c = deploy(direct_deploy)

    c.open_watch(
        "https://LEFT.TEST/a#fragment",
        "https://RIGHT.TEST/b/",
        " IANA ",
        "1",
    )

    rec = watch(c)
    assert rec["left_url"] == "https://left.test/a"
    assert rec["right_url"] == "https://right.test/b"
    assert rec["field"] == "iana"
    assert rec["status"] == "OPEN"


def test_second_recheck_cannot_pay_twice(
    direct_vm, direct_deploy, direct_alice
):
    mock_pages(
        direct_vm,
        "<p>iana</p>",
        "<p>iana</p>",
    )
    direct_vm.value = BOND
    c = deploy(direct_deploy)

    with direct_vm.prank(direct_alice):
        c.open_watch(LEFT, RIGHT, "iana", "1")

        direct_vm.clear_mocks()
        direct_vm.mock_web(
            r"https://left\.test",
            {"status": 200, "body": "<p>iana</p>"},
        )
        direct_vm.mock_web(
            r"https://right\.test",
            {"status": 200, "body": "<p>other</p>"},
        )
        c.recheck("1")

        with direct_vm.expect_revert("not open"):
            c.recheck("1")


def test_missing_watch_returns_empty_json(
    direct_vm, direct_deploy
):
    c = deploy(direct_deploy)
    assert c.get_watch("999") == "{}"
    assert c.next_watch() == "1"

def test_second_account_can_catch_split(direct_vm, direct_deploy, direct_alice, direct_bob):
    mock_pages(
        direct_vm,
        "<p>iana keeps this zone</p>",
        "<p>iana is also here</p>",
    )
    direct_vm.value = BOND
    c = deploy(direct_deploy)

    with direct_vm.prank(direct_alice):
        c.open_watch(LEFT, RIGHT, "iana", "1")

    direct_vm.clear_mocks()
    direct_vm.mock_web(
        r"https://left\.test",
        {"status": 200, "body": "<p>iana keeps this zone</p>"},
    )
    direct_vm.mock_web(
        r"https://right\.test",
        {"status": 200, "body": "<p>no token here</p>"},
    )

    with direct_vm.prank(direct_bob):
        c.recheck("1")

    rec = watch(c)
    assert rec["status"] == "SPLIT"
    assert rec["funder"].lower() == "0x" + direct_alice.hex().lower()
    assert rec["finder"].lower() == "0x" + direct_bob.hex().lower()


def test_matching_pages_stay_open(direct_vm, direct_deploy, direct_alice):
    mock_pages(
        direct_vm,
        "<p>iana keeps this zone</p>",
        "<p>iana is also here</p>",
    )
    direct_vm.value = BOND
    c = deploy(direct_deploy)

    with direct_vm.prank(direct_alice):
        c.open_watch(LEFT, RIGHT, "iana", "1")
        c.recheck("1")

    rec = watch(c)
    assert rec["status"] == "OPEN"
    assert rec["left_value"] == "yes"
    assert rec["right_value"] == "yes"
    assert rec["finder"].lower() == "0x0000000000000000000000000000000000000000"


def test_funder_can_refund_after_deadline(direct_vm, direct_deploy, direct_alice):
    mock_pages(
        direct_vm,
        "<p>iana keeps this zone</p>",
        "<p>iana is also here</p>",
    )
    direct_vm.value = BOND
    c = deploy(direct_deploy)

    with direct_vm.prank(direct_alice):
        c.open_watch(LEFT, RIGHT, "iana", "1")

    rec = watch(c)
    deadline = int(rec["deadline"])

    from datetime import datetime, timezone

    direct_vm.warp(
        datetime.fromtimestamp(
            deadline + 1,
            tz=timezone.utc,
        ).isoformat().replace("+00:00", "Z")
    )

    with direct_vm.prank(direct_alice):
        c.refund("1")

    rec = watch(c)
    assert rec["status"] == "REFUNDED"
    assert rec["finder"].lower() == "0x0000000000000000000000000000000000000000"
    assert rec["amount"] == str(BOND)

def test_rejects_malformed_hours(direct_vm, direct_deploy):
    mock_pages(
        direct_vm,
        "<p>iana keeps this zone</p>",
        "<p>iana is also here</p>",
    )
    direct_vm.value = BOND
    c = deploy(direct_deploy)

    with direct_vm.expect_revert("window must be an integer"):
        c.open_watch(LEFT, RIGHT, "iana", "abc")


def test_rejects_http_url(direct_vm, direct_deploy):
    direct_vm.value = BOND
    c = deploy(direct_deploy)

    with direct_vm.expect_revert("https url required"):
        c.open_watch("http://left.test/a", RIGHT, "iana", "1")


def test_rejects_url_with_whitespace(direct_vm, direct_deploy):
    direct_vm.value = BOND
    c = deploy(direct_deploy)

    with direct_vm.expect_revert("https url required"):
        c.open_watch("https://left.test/a bad", RIGHT, "iana", "1")


def test_rejects_empty_or_malformed_host(direct_vm, direct_deploy):
    direct_vm.value = BOND
    c = deploy(direct_deploy)

    with direct_vm.expect_revert("https url required"):
        c.open_watch("https:///a", RIGHT, "iana", "1")

    with direct_vm.expect_revert("https url required"):
        c.open_watch("https://:443/a", RIGHT, "iana", "1")


def test_rejects_window_above_maximum(direct_vm, direct_deploy):
    direct_vm.value = BOND
    c = deploy(direct_deploy)

    with direct_vm.expect_revert("window must be 1-168 hours"):
        c.open_watch(LEFT, RIGHT, "iana", "169")


def test_split_fee_math_is_exact(direct_vm, direct_deploy, direct_alice, direct_bob):
    mock_pages(
        direct_vm,
        "<p>iana keeps this zone</p>",
        "<p>iana is also here</p>",
    )
    direct_vm.value = BOND
    c = deploy(direct_deploy)

    with direct_vm.prank(direct_alice):
        c.open_watch(LEFT, RIGHT, "iana", "1")

    direct_vm.clear_mocks()
    direct_vm.mock_web(
        r"https://left\.test",
        {"status": 200, "body": "<p>iana keeps this zone</p>"},
    )
    direct_vm.mock_web(
        r"https://right\.test",
        {"status": 200, "body": "<p>no token here</p>"},
    )

    with direct_vm.prank(direct_bob):
        c.recheck("1")

    rec = watch(c)

    gross = BOND
    fee = gross * 500 // 10000
    finder_amount = gross - fee

    assert gross == BOND
    assert fee == BOND // 20
    assert finder_amount == BOND - (BOND // 20)
    assert rec["status"] == "SPLIT"
    assert rec["amount"] == str(gross)
    assert rec["finder"].lower() == "0x" + direct_bob.hex().lower()


def test_refund_requires_deadline(direct_vm, direct_deploy, direct_alice):
    mock_pages(
        direct_vm,
        "<p>iana keeps this zone</p>",
        "<p>iana is also here</p>",
    )
    direct_vm.value = BOND
    c = deploy(direct_deploy)

    with direct_vm.prank(direct_alice):
        c.open_watch(LEFT, RIGHT, "iana", "1")

    with direct_vm.prank(direct_alice):
        with direct_vm.expect_revert("wait for the window"):
            c.refund("1")

