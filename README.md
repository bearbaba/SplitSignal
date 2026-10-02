# SplitSignal

A Studionet pool that locks GEN on two https pages and one field.

Deployed contract: `0x07aeE113dD0248DB23BC0259ba1197D0cFC9e15b`

Watch 1 is OPEN: both IANA pages matched `iana` at open, 1 GEN reserved until 21:55 on 3 Oct 2026. A pair that already differs reverts with `already split` and does not reserve funds.

`recheck` pays the caller 95% when the frozen values diverge. Five percent stays in the pool. `refund` returns an open bond to the funder after the window. Neither path has a successful transaction yet.

App: https://splitsignal-ten.vercel.app/
