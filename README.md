# SplitSignal

SplitSignal is a GenLayer intelligent contract that watches two HTTPS pages for a token-presence split.

## Contract behavior

A watch is created only when:

- both URLs are HTTPS;
- the URLs are different after normalization;
- the field token is 3-32 characters;
- the watch window is 1-168 hours;
- the bond is at least `10**16`;
- both pages are readable;
- both pages currently contain the requested token.

The contract records the matching `yes/yes` observation and opens the watch.

A later `recheck()` compares the same two pages:

- `yes/yes` keeps the watch `OPEN`;
- `yes/no` or `no/yes` changes it to `SPLIT`;
- the account that performs the successful recheck becomes the `finder`;
- 95% of the bond is paid to the finder;
- 5% is paid to the deployer's `fee_to` address;
- the state is written as `SPLIT` before the payout calls, preventing a second successful payout.

If the watch reaches its deadline while still `OPEN`, anyone may call `refund()` and the original funder receives the full bond.

## Important scope

The contract checks **token presence**, not a numeric value extracted from a page.

For example, the field `iana` is treated as:

- `yes` if the normalized rendered page contains the token;
- `no` otherwise.

This is intentionally a small, auditable proof primitive rather than a general web scraper.

## Tests

The local Direct Mode suite covers:

- URL and field validation;
- malformed window input;
- window bounds;
- minimum bond;
- unreadable pages;
- normalized URLs;
- opening only when both pages agree;
- matching pages remaining `OPEN`;
- a different account catching a split;
- finder/funder attribution;
- one-time split settlement;
- deadline-gated refund;
- exact 5% fee / 95% finder arithmetic.

The current local suite passes completely.

Direct Mode does not execute the `EthSend` operation used by the contract's transfer interface, so local tests verify the payout-triggering state transition and accounting invariants rather than pretending to prove network balance movement. Actual payout/refund settlement must be verified on the deployed network.

## Deployment

The frontend is configured separately from the contract address. After a new deployment, update the configured contract address in the public app before publishing.

## App

https://splitsignalv2.vercel.app/

## Project Evidence

### SplitSignal workflow

Create → Hunt → Claim → Refund.

The live application explains the complete Watch lifecycle, including protocol limits and bounty settlement.

### GenLayer Intelligent Contract

- Contract: `0x68d058A66f486adeeF845785540f9056bc9E9E87`
- Explorer: https://explorer-studio.genlayer.com/address/0x68d058A66f486adeeF845785540f9056bc9E9E87
- Live app: https://splitsignalv2.vercel.app/

The GenLayer Studio Explorer shows finalized and accepted deployment, `open_watch`, and `recheck` transactions.

## Why GenLayer

SplitSignal needs more than a traditional smart contract. The protocol must read public web sources, compare real-world information, reach validator consensus on the observation, and then enforce the result on-chain.

GenLayer is central to that workflow.

## 60-second demo

1. Open the live app and connect a wallet.
2. Click **Try demo**.
3. Create the demo Watch while both sources match.
4. Click **Change Source B**.
5. Recheck the Watch.
6. If GenLayer verifies the divergence, the Watch becomes `SPLIT` and the finder reward is triggered.

Live app: https://splitsignalv2.vercel.app/

Contract:
`0x68d058A66f486adeeF845785540f9056bc9E9E87`

Explorer:
https://explorer-studio.genlayer.com/address/0x68d058A66f486adeeF845785540f9056bc9E9E87

## Architecture

User
→ SplitSignal UI
→ GenLayer Intelligent Contract
→ Public Source A + Public Source B
→ Validator consensus
→ OPEN / SPLIT / REFUNDED
→ Bounty settlement
