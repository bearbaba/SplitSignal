# SplitSignal

**A permissionless bounty protocol that rewards anyone who verifies when two public sources stop agreeing.**

SplitSignal is built on GenLayer and turns public-source divergence into a verifiable, economically incentivized signal.

Users create a Watch by choosing two public HTTPS sources, a signal to monitor, an active duration, and a GEN bounty. The Intelligent Contract only opens the Watch when both sources initially agree.

Anyone can recheck the Watch while it is active. If GenLayer verifies that the two sources have diverged, the Watch becomes `SPLIT` and the finder reward is triggered. If no divergence is verified before expiry, the funder can reclaim the bounty.

## Live Project

- App: https://splitsignalv2.vercel.app/
- Demo video: https://youtu.be/Rzw-AcIbncc
- GitHub: https://github.com/bearbaba/SplitSignal
- Explorer: https://explorer-studio.genlayer.com/address/0x68d058A66f486adeeF845785540f9056bc9E9E87
- Studio: https://studio.genlayer.com/?import-contract=0x68d058A66f486adeeF845785540f9056bc9E9E87

## Intelligent Contract

`0x68d058A66f486adeeF845785540f9056bc9E9E87`

Deployed on GenLayer Studionet.

## Why GenLayer

SplitSignal needs more than a traditional deterministic smart contract.

Its core workflow depends on reading public web sources, observing whether a monitored signal is present, comparing the two sources, reaching validator consensus, and then enforcing the result on-chain.

GenLayer is central to the product because it allows the contract to read public HTTPS sources, evaluate real-world web content, reach consensus on the observation, update Watch state, and trigger settlement from the verified result.

Without GenLayer, SplitSignal would need a centralized oracle or trusted backend to decide whether the two sources still agree.

## How It Works

1. A user creates a Watch.
2. Two public sources are selected.
3. The sources must initially agree.
4. A GEN bounty becomes active.
5. Anyone can recheck the Watch while it is active.
6. GenLayer reads both sources again.
7. If they still agree, the Watch remains `OPEN`.
8. If they diverge, the Watch becomes `SPLIT`.
9. The finder receives 95% of the bounty.
10. The protocol receives a 5% fee.
11. If no split is verified before expiry, the funder can reclaim the bounty.

## Active Duration

The selected duration is how long the bounty stays open.

It is **not** a waiting period.

A Watch can be rechecked immediately after creation or at any later point before expiry.

For example, if a Watch is active for 24 hours and Source B changes after only two minutes, anyone can recheck it immediately. If GenLayer verifies that the two sources now disagree, the Watch can become `SPLIT` right away.

The active duration simply defines how long the bounty remains available before expiry.

## Bounty Economics

- Minimum bounty: `0.01 GEN`
- Finder reward: `95%`
- Protocol fee: `5%`
- Expired OPEN Watch: the funder can reclaim the bounty

The reward is paid for verifying a divergence, not for waiting a fixed amount of time.

## Guided Demo

The live app includes a guided demo flow.

1. Connect a wallet.
2. Click **Try demo**.
3. Two public demo sources are created with matching values.
4. Create the Watch.
5. Click **Change Source B**.
6. Recheck the Watch.
7. GenLayer reads both public sources again.
8. The divergence is verified.
9. The Watch becomes `SPLIT`.
10. The finder reward is triggered.

The demo sources are public so GenLayer validators can independently inspect the same content.

## Watch Lifecycle

### OPEN

The Watch is active and no verified divergence has been recorded yet.

### SPLIT

GenLayer verified that the monitored sources no longer agree.

The successful verifier becomes the finder and the payout is triggered.

### REFUNDED

The Watch expired without a verified split and the funder reclaimed the bounty.

## Discovering Watches

The frontend supports:

- recent Watches
- open bounty discovery
- ending-soon sorting
- highest-bounty sorting
- My Watches
- My Claims
- All Watches
- pagination through historical Watches
- direct lookup by Watch ID

Historical Watches remain stored in the contract even if they are no longer visible on the first page.

## Trust Boundary

SplitSignal verifies **whether two public sources agree or disagree**.

It does not determine which source represents absolute truth.

For example:

Source A says:

`yes`

Source B says:

`no`

SplitSignal can verify:

`Source A != Source B`

It does not claim that `yes` or `no` is objectively correct.

This distinction is intentional.

SplitSignal is designed as a monitoring and bounty primitive for detecting changes or conflicts across public information sources.

## Potential Use Cases

SplitSignal can be used to monitor:

- public announcements
- governance pages
- status pages
- API outputs
- terms and policy pages
- public datasets
- project documentation
- protocol information
- mirrored information sources
- public records where disagreement itself is meaningful

The core question is simple:

> When two public sources stop agreeing, who notices first?

## Main Contract Actions

### `open_watch`

Creates a new Watch when both public sources initially agree.

The call includes:

- Source A URL
- Source B URL
- monitored field or token
- active duration
- GEN bounty

### `recheck`

Reads both sources again.

If the observations diverge while the Watch is still active:

- status becomes `SPLIT`
- finder becomes the caller
- 95% of the bounty goes to the finder
- 5% goes to the protocol

Settlement happens as part of the successful recheck flow.

### `refund`

After an OPEN Watch expires, the original funder can reclaim the bounty.

### `get_watch`

Returns the stored state for a specific Watch ID.

## Frontend Transaction Flow

The frontend tracks the transaction lifecycle from wallet approval to confirmed on-chain state.

The basic flow is:

`Waiting for wallet → Submitted → Confirming → Confirmed`

After confirmation, the frontend reloads the accepted Watch state instead of assuming the result locally.

## Architecture

User  
↓  
SplitSignal Frontend  
↓  
GenLayer Intelligent Contract  
↓  
Public Source A + Public Source B  
↓  
Validator Consensus  
↓  
Watch State  
↓  
`OPEN / SPLIT / REFUNDED`  
↓  
Economic Settlement

## Product Principles

SplitSignal is designed around a few simple ideas:

- public evidence
- verifiable divergence
- permissionless rechecking
- economic incentive for discovery
- consensus-based settlement
- no trusted operator deciding the result
- expiry and refund so funds are not locked forever

## Current Scope

SplitSignal is currently deployed on GenLayer Studionet.

The complete product flow is:

`Create → Monitor → Detect → Recheck → Verify → Reward`

The current version demonstrates the full end-to-end protocol loop with a real Intelligent Contract, wallet interaction, public source inspection, transaction lifecycle handling, bounty settlement, Watch discovery, history browsing, direct Watch lookup, and a reproducible guided demo.

For larger-scale production use, future improvements could include dedicated indexing, source-quality reputation, analytics, alerts, and additional anti-spam systems.

Those are scaling improvements. The core protocol flow already works end to end.

## Project Links

- Live app: https://splitsignalv2.vercel.app/
- Demo video: https://youtu.be/Rzw-AcIbncc
- GitHub: https://github.com/bearbaba/SplitSignal
- Contract Explorer: https://explorer-studio.genlayer.com/address/0x68d058A66f486adeeF845785540f9056bc9E9E87
- Studio import: https://studio.genlayer.com/?import-contract=0x68d058A66f486adeeF845785540f9056bc9E9E87

## Status

SplitSignal is live on GenLayer Studionet and the end-to-end flow has been tested successfully:

`Create Watch → Sources Match → Change Source B → Recheck → SPLIT → Finder Reward`

---

**SplitSignal — Watch. Verify. Reward.**
