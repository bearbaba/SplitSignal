# Architecture

SplitSignal pays an account for catching two public pages diverge.
The app does not decide. It only sends transactions and reads state.

## Why GenLayer

The two pages are not on-chain. A normal contract cannot open them.
Validators each render both URLs and must agree on the two field values.
The payout is a direct result of that agreement.

An LLM is not used. The field is an exact token the funder chose.
Consensus is strict_eq on canonical JSON.

## Money

open_watch is payable. The amount is stored on the watch.
recheck writes SPLIT before the transfer. A second recheck reverts.
refund writes REFUNDED before the transfer. It is refused for the first hour.

AGREED does not move money. An unreadable page does not move money.

## Roles

- Funder locks GEN and chooses both URLs and the field. Those three cannot change.
- Finder is whoever calls recheck and receives the bond if the values differ.
- Anyone can refund an still-open watch after one hour.

## Live proof

Watch 1 on 0x03EFaa8148120C025b29c9B09dE0CB0c4Fb7d46d:
- left https://example.org = yes
- right https://info.cern.ch = no
- field iana
- amount 1 GEN
- status SPLIT
- finder 0x4C7cb73aC8F8999af21cfc9fF4cF2333a9508Dcb

## Limits

The field check is a token search, not a reading of the page's meaning.
A refund after one hour does not require the pages to still be unreadable.
Payout uses emit_transfer and settles when the transaction finalizes.
