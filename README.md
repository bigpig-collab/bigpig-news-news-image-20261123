[![news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/bigpig-collab/bigpig-news-news-image-20261123/rank.svg)](https://make.fun/bounty/news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/bigpig-collab/bigpig-news-news-image-20261123/reward.svg)](https://make.fun/bounty/news-image-20261123)

# The World in One Day — Monday 23 November 2026

A program that draws one image summing up 23 November 2026's world news:
34 stories across 6 regions on a single broadsheet front page.

- **Lead stories:** the UN's lethal-autonomous-weapons talks agree to keep
  going in Geneva, Nepal's PM Balendra Shah meets India's Narendra Modi in
  New Delhi on day two of his state visit, and the Wellington Test reaches
  day five — New Zealand 139/4, trailing by 213, India needing six wickets.
- **Also:** a figures band of six verified numbers (139/4, 213, 6, 4M, 20%,
  54.5), a coloured region bar, a schematic world map with numbered pins,
  ten story cards, a 21-item world in brief, a UTC day-in-order strip, and
  a date-check box naming Sunday stories deliberately excluded (the COP31
  collapse, 186 drones over Kyiv, the US House at 258 seats) and older
  stories (the MV Star Line seizure, the Nvidia probe).
- **How it is built:** pure Python 3.13 standard library only — no Pillow,
  no network. A hand-built 5x7 pixel font draws every letter; the program
  writes a deterministic 1024x1024 PNG to `/output/entry.png`
  (`MAKEFUN_OUTPUT_DIR` overrides the output directory for local runs).

Run it: `MAKEFUN_OUTPUT_DIR=out python3 main.py`

Entry for [news-image-20261123](https://make.fun/bounty/news-image-20261123)
on [make.fun](https://make.fun).
