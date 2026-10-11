# SplitSignal

**A permissionless bounty protocol that rewards anyone who verifies when two public sources stop agreeing.**

SplitSignal is built on GenLayer and turns public-source divergence into a verifiable, economically incentivized signal.

Users create a Watch by choosing two public HTTPS sources, a signal to monitor, an active duration, and a GEN bounty. The Intelligent Contract only opens the Watch when both sources initially agree.

Anyone can recheck the Watch while it is active. If GenLayer verifies that the two sources have diverged, the Watch becomes `SPLIT` and the finder reward is triggered. If no divergence is verified before expiry, the funder can reclaim the bounty.

## Live Project

- App: https://splitsignalv2.vercel.app/
- Demo video: https://youtu.be/Rzw-AcIbncc
- GitHub: https://github.com/bearbaba/SplitSignal
- Explorer: https://explorer-studio.genlayer.com/address/0x4611458C93a66fee5d4F2f050E80671c170d89C5
- Studio: https://studio.genlayer.com/?import-contract=0x4611458C93a66fee5d4F2f050E80671c170d89C5

## Intelligent Contract

`0x4611458C93a66fee5d4F2f050E80671c170d89C5`

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
5. A finder commits a recipient-bound split claim while the Watch is active.
6. After a short anti-front-run delay, the finder reveals the claim and GenLayer reads both sources again.
7. If they still agree, the Watch remains `OPEN`.
8. If they diverge, the Watch becomes `SPLIT`.
9. The finder receives 95% of the bounty.
10. The protocol receives a 5% fee.
11. If no split is verified before expiry, the funder can reclaim the bounty.

## Active Duration

The selected duration is how long the bounty stays open.

It is **not** a waiting period.

A finder can commit a split claim immediately after creation or at any later point before expiry. The reveal/recheck is accepted only after the short anti-front-run commitment delay.

For example, if a Watch is active for 24 hours and Source B changes after only two minutes, a finder can secure the claim immediately, wait through the commitment delay, then reveal/recheck. If GenLayer verifies that the two sources now disagree, the Watch becomes `SPLIT`.

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
6. Click **Recheck and claim** to submit the recipient-bound split commitment.
7. After the anti-front-run delay, approve the reveal/recheck transaction.
8. GenLayer reads both public sources again.
9. The divergence is verified.
10. The Watch becomes `SPLIT`.
11. The committed payout recipient receives the finder reward.

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
- finder becomes the payout recipient bound into the prior commitment
- 95% of the bounty goes to that committed recipient
- 5% goes to the protocol

Settlement happens as part of the successful reveal/recheck flow. A copied reveal cannot redirect the reward because the commitment is keyed to the reporter and binds the payout recipient.

### `refund`

After an OPEN Watch expires, the original funder can reclaim the bounty.

### `get_watch`

Returns the stored state for a specific Watch ID.

## Frontend Transaction Flow

The frontend tracks the transaction lifecycle from wallet approval to confirmed on-chain state.

The basic flow is:

`Commit claim → Accepted commitment → Anti-front-run delay → Reveal/recheck → Confirmed`

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

Those are scaling improvements. The core protocol flow is implemented; final live end-to-end verification against the current Studionet deployment is the remaining release step.

## Project Links

- Live app: https://splitsignalv2.vercel.app/
- Demo video: https://youtu.be/Rzw-AcIbncc
- GitHub: https://github.com/bearbaba/SplitSignal
- Contract Explorer: https://explorer-studio.genlayer.com/address/0x4611458C93a66fee5d4F2f050E80671c170d89C5
- Studio import: https://studio.genlayer.com/?import-contract=0x4611458C93a66fee5d4F2f050E80671c170d89C5

## Status

The security-hardened SplitSignal contract is deployed on GenLayer Studionet. Repository security and browser regressions pass for the recipient-bound commit/reveal flow.

Live end-to-end verification completed successfully on the current deployment on October 11, 2026:

`Create Watch → Sources Match → Change Source B → Commit claim → Reveal/recheck → SPLIT → Finder Reward`

Watch #1 reached `SPLIT` on-chain and triggered the 0.0095 GEN finder reward for `0x4C7cb73aC8F8999af21cfc9fF4cF2333a9508Dcb`.

---

**SplitSignal — Watch. Verify. Reward.**
