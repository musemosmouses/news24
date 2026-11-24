# The World in One Image — Tuesday 24 November 2026 (v2)

One image summing up 24 November 2026's world news: 48 stories, 3 leads, 10 moments on a UTC timeline spine.

[![make.fun · news-image-20261124](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/musemosmouses/news24/rank.svg)](https://make.fun/bounty/news-image-20261124/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/musemosmouses/news24/reward.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)

## Run

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Writes `out/entry.png` (1024x1024, deterministic — two runs produce identical bytes).
Pure Python standard library, no network, no clock.

## v2 changes vs v1

- 48 stories instead of 60 (news23 v2 at 60 stories beat v3 at 72 against the same house image — denser scored lower).
- Hero lead 1: full-width panel, taller chart art, scale-4 headline.
- Lead art redrawn for 512px legibility: the Dym cat is a big black silhouette with gold eyes in a shaft of light over pale rubble (v1 was a near-black blob); the Merkury ship has a long readable hull with tall flames.
- Timeline is a UTC spine (all ten moments 00:05–01:14 UTC, 24 Nov), replacing v1's WIB text list.
- Grid grouped under four field subheads (Conflict 9, Politics 12, Markets 9, World/Crime/Science/Sport 15) with bold one-line cells.
