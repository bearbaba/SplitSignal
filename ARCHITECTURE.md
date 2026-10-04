# SplitSignal Architecture

## 1. Overview

SplitSignal is a single GenLayer intelligent contract plus a small browser client.

The contract creates a funded watch over two HTTPS sources. A watch is valid only when both sources are readable and both currently contain the same token.

The watch can then end in one of three meaningful states:

- `OPEN` — sources still agree or have not yet diverged;
- `SPLIT` — a successful recheck found different token-presence results;
- `REFUNDED` — the deadline passed without a split and the bond was returned to the funder.

There is no `AGREED` status in the implementation.

## 2. Data model

Each watch stores:

- funder;
- finder;
- normalized left URL;
- normalized right URL;
- token field;
- bond amount;
- opening timestamp;
- deadline;
- last observed left value;
- last observed right value;
- status;
- human-readable note.

The watch identifier is a monotonically increasing string derived from `next_id`.

## 3. Opening a watch

`open_watch(left_url, right_url, field, hours)`:

1. validates and normalizes both HTTPS URLs;
2. validates the token field;
3. parses and bounds the watch window;
4. checks the attached bond;
5. reads both pages through GenLayer nondeterministic web access;
6. requires both pages to be readable;
7. requires both token-presence results to match;
8. stores the watch as `OPEN`.

A watch cannot be opened against two identical normalized URLs.

## 4. Rechecking

`recheck(watch_id)` is callable by any account while the watch is `OPEN` and before its deadline.

The contract reads both sources again under the same equivalence-principle wrapper.

If both results still agree, the watch remains `OPEN`.

If they differ:

1. the watch becomes `SPLIT`;
2. the caller becomes `finder`;
3. the result values are stored;
4. the finder receives 95% of the bond;
5. `fee_to` receives 5%.

The state transition happens before the transfer calls. Therefore a second recheck cannot successfully settle the same watch.

## 5. Refunds

`refund(watch_id)` requires:

- status `OPEN`;
- current time at or after the deadline.

The entire bond is then paid to the original `funder` and the watch becomes `REFUNDED`.

The function does not require the caller to be the funder; the payment recipient is always the stored funder.

## 6. Web observation

The web predicate is deliberately simple.

The rendered HTML is lowercased and searched for the requested token using whitespace-delimited token matching.

This is **presence detection**, not semantic extraction and not a numeric price/value comparison.

## 7. Deterministic state vs nondeterministic I/O

The contract keeps web access inside nondeterministic execution and compares the normalized result through `strict_eq`.

Persistent watch state is updated only after the web result has been obtained.

## 8. Testing boundary

Direct Mode provides deterministic mocks for web responses and controllable time.

The local test suite therefore proves the contract state machine and validation behavior, including:

- opening;
- matching observations;
- divergence;
- cross-account discovery;
- one-time settlement;
- deadline refund;
- invalid input.

The installed Direct Mode harness does not execute the `EthSend` operation emitted by the transfer interface. Consequently, local tests do not claim to prove actual network balance movement.

Actual payout/refund settlement is a deployment-level verification item.

## 9. Frontend

The browser client:

- reads the configured contract;
- discovers the next watch identifier;
- loads individual watch state;
- submits `open_watch`;
- submits `recheck`;
- submits `refund`;
- refreshes the displayed state after writes.

The UI should never treat a hardcoded historical watch ID as the canonical current watch.

## 10. Security/economic assumptions

The contract does not guarantee that either web page is truthful.

It only records whether the requested token is present in the rendered response observed by the GenLayer execution.

The economic incentive is:

- funder deposits the bond;
- any observer may recheck;
- a successful diverging observation earns 95% of the bond;
- the deployer receives 5%;
- no successful divergence means the funder can recover the full bond after the deadline.

The payout recipient for a split is the successful recheck caller, not the funder.

## 11. Known verification boundary

The most important deployment-level check is actual value movement.

Before presenting the deployed contract as fully verified, execute:

1. fund a watch;
2. have account A open it;
3. have account B trigger the split;
4. confirm B receives 95%;
5. confirm `fee_to` receives 5%;
6. confirm a second recheck fails;
7. open a second watch;
8. let its deadline pass;
9. confirm the funder receives the full refund.
