# SplitSignal

A bond that pays the account catching two public pages diverge.

A funder locks GEN against two URLs and one field. Anyone can recheck.
Validators render both pages. If the field values differ, the finder is paid.
If they still match, the watch stays AGREED and the bond stays put.
An open watch can be refunded after one hour.

This is not a warranty desk and not a delivery escrow.
The question is whether two public sources still say the same thing.

## Live

- Network: Studionet
- Contract: 0x03EFaa8148120C025b29c9B09dE0CB0c4Fb7d46d
- Studio: https://studio.genlayer.com/?import-contract=0x03EFaa8148120C025b29c9B09dE0CB0c4Fb7d46d
- Explorer: https://explorer-studio.genlayer.com/address/0x03EFaa8148120C025b29c9B09dE0CB0c4Fb7d46d
- App: the deployed Vercel URL

## Proven watch

| Field | Value |
| --- | --- |
| id | 1 |
| left | https://example.org = yes |
| right | https://info.cern.ch = no |
| token | iana |
| amount | 1 GEN |
| status | SPLIT |

## Methods

| Method | Who | Effect |
| --- | --- | --- |
| open_watch | funder, payable | locks GEN, freezes both URLs and the field |
| recheck | anyone | SPLIT pays the caller, AGREED keeps the bond |
| refund | anyone, after 1 hour | returns an open bond to the funder |
| get_watch | anyone | reads the watch |

## Files

- contracts/SplitSignal.py
- index.html
- ARCHITECTURE.md
