# Reviewer Evidence — SplitSignal

This file maps the steward's requested fixes to the implementation, repository regressions, and live Studionet verification for the current release.

## Current release

- Production app: https://splitsignalv2.vercel.app/
- Current reviewer demo: https://youtu.be/ckpq1BAuDP0
- Studionet contract: `0x4611458C93a66fee5d4F2f050E80671c170d89C5`
- Studio import: https://studio.genlayer.com/?import-contract=0x4611458C93a66fee5d4F2f050E80671c170d89C5
- Explorer: https://explorer-studio.genlayer.com/address/0x4611458C93a66fee5d4F2f050E80671c170d89C5
- Security/board PR: https://github.com/bearbaba/SplitSignal/pull/1
- Merged to `main` as: `3bc9540700f3e09d8a223335bf2fb5e6fa1ec83f`

## Steward request → implementation → evidence

### 1. Bind a reported split and payout recipient so a copied/front-run recheck cannot take the discoverer's reward

Implementation: `contracts/SplitSignal.py`

- `commit_split(watch_id, commitment)` stores a commitment under a reporter-specific key.
- The commitment digest binds `watch_id | payout_recipient | salt`.
- `recheck(watch_id, payout_recipient, salt)` recomputes the digest and rejects a mismatched recipient.
- A 30-second minimum commitment age prevents a copied reveal from being paired with a same-instant attacker commitment.
- The finder and payout use the recipient that was bound into the commitment.
- The legacy Studionet runner's string-decoded public `Address` argument is normalized with `Address(payout_recipient)` before Address storage or payout.

Repository regression: `tests/test_front_run_regression.py`

- `test_copied_or_front_run_reveal_cannot_redirect_discoverer_reward`
- `test_commitment_is_bound_to_watch_and_recipient`

The regression covers:
- copied commitment under a different reporter,
- attempted payout redirection,
- copied reveal that can only preserve the originally bound recipient,
- payout split to finder/protocol,
- runtime-style string-decoded payout recipient normalization.

### 2. Repair the bounty board so refresh and pagination preserve their controls

Implementation: `public/index.html`

- Pager controls are outside the replaceable bounty-list render target.
- Refresh reloads the current `huntPage` instead of resetting the page.
- Pagination remains usable after rendering and refresh.

Browser regression: `tests/browser/bounty-board.spec.mjs`

The Playwright regression verifies:
- multi-page navigation,
- controls remain present after page changes,
- refresh preserves the current page.

### 3. Render all contract-stored fields and URLs without HTML interpretation

Implementation: `public/index.html`

Contract-provided values are rendered through DOM nodes and `textContent`, not interpolated HTML. Stored URLs are only made clickable after HTTPS validation.

The board exposes every `get_watch` field:

`id, funder, finder, left_url, right_url, field, amount, opened_at, deadline, left_value, right_value, status, note`

Browser regression: `tests/browser/bounty-board.spec.mjs`

The test injects HTML-like values into contract fields/URLs and verifies:
- they remain literal text,
- no injected `img` or `svg` element is created,
- the test payload does not execute,
- the selected-Watch metadata path remains text-only.

## Front-run threat cases

| Case | Result |
| --- | --- |
| Attacker copies another reporter's commitment | Stored under the attacker's reporter-specific key; does not become the victim's claim |
| Attacker changes payout recipient during reveal | Commitment digest mismatch |
| Attacker copies the reveal byte-for-byte | The payout recipient remains the one already bound into the digest |
| Attacker sees a reveal and creates a matching commitment immediately | Minimum commitment age blocks the immediate reveal |
| Legacy runner passes the payout address as a string | Contract normalizes it to `Address` before storing/paying |

## CI evidence

The final PR head used for live verification was `079558a62b0ebababb794b989ff4e6e98fe37d99`.

Both required repository regressions passed before merge:

- Contract security regression — run 22: https://github.com/bearbaba/SplitSignal/actions/runs/38105469852
- Browser regression — run 25: https://github.com/bearbaba/SplitSignal/actions/runs/38105469837

The PR was then squash-merged to `main` as `3bc9540700f3e09d8a223335bf2fb5e6fa1ec83f`.

## Live Studionet verification

Live end-to-end verification completed successfully on October 11, 2026 against the current contract deployment.

Flow:

`Create Watch → Sources Match → Change Source B → Commit claim → 30s+ delay → Reveal/recheck → SPLIT → Finder Reward`

Observed result:

- Watch: `#1`
- Status: `SPLIT`
- Finder: `0x4C7cb73aC8F8999af21cfc9fF4cF2333a9508Dcb`
- Finder reward triggered: `0.0095 GEN`
- Settlement message: `SPLIT VERIFIED ON-CHAIN`

This live run also exercised the runtime Address-normalization fix on the deployed Studionet contract.

### Independent on-chain check

A reviewer can independently import the current contract in Studio and call:

`get_watch("1")`

Expected accepted state:

- `status = "SPLIT"`
- `finder = "0x4C7cb73aC8F8999af21cfc9fF4cF2333a9508Dcb"`
- `left_value = "yes"`
- `right_value = "no"`
- `note = "sources diverged; payout bound to committed recipient"`
- `amount = "10000000000000000"` (0.01 GEN original bounty)

The UI reports the corresponding finder reward as `0.0095 GEN`, matching the contract's 95% finder / 5% protocol split.

## Reproduce repository checks

Security regression:

```bash
python -m pip install -r requirements.txt
python -m pytest -q tests/test_front_run_regression.py
```

Browser regression:

```bash
npm install
npx playwright install chromium
npm run test:browser
```

## Demo evidence

Current reviewer demo: https://youtu.be/ckpq1BAuDP0

The current video demonstrates the security-hardened flow on the active deployment: Watch creation while sources agree, Source B divergence, recipient-bound `commit_split`, the anti-front-run commitment delay, reveal/recheck, GenLayer consensus, and successful on-chain `SPLIT` settlement with the finder reward.

The older one-step recheck video predates the recipient-bound commit/reveal change and is superseded by the current reviewer demo above.

## Trust boundary

SplitSignal verifies whether two public sources agree or disagree. It does not claim which source is objectively true. Settlement rewards the first valid reporter of a verified divergence under the commit/reveal rules.
