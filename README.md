# SplitSignal

Studionet contract `0x9643A50a9645A3CF90CDC188b44f71Ec07C141b6`.

A watch opens only when two https pages contain the same field token. The bond is the transaction value. Recheck pays the caller 95 percent if the pages differ before the deadline. Five percent goes to the deployer. Refund returns an open bond to the funder after the deadline.

Proven on this contract: watches 1 and 2 were refunded after the window. Watch 4 opened on two pages that both contained `iana`, then the right page was changed. Recheck returned left `yes`, right `no`, status `SPLIT`. The funder and finder were the same account.

Not proven: a second account catching the split. The check is token presence, not a value cut from the page. An older pool contract at `0x07aeE113dD0248DB23BC0259ba1197D0cFC9e15b` is a different book.

App: https://splitsignal-ten.vercel.app/
