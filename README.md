[![news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/bigpig-collab/bigpig-news-news-image-20261123/rank.svg)](https://make.fun/bounty/news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/bigpig-collab/bigpig-news-news-image-20261123/reward.svg)](https://make.fun/bounty/news-image-20261123)

# The World in One Day — Monday 23 November 2026 (Evening Edition)

A program that draws one image summing up 23 November 2026's world news
as the day ended — outcomes first, not forecasts: 34 stories across
6 regions on a single evening-edition front page.

- **Lead stories:** the Wellington Test ends in a draw (New Zealand
  239/5 hold India after 720/9 declared), Modi and Shah agree a
  24,000-crore package for Nepal plus a new Ayodhya–Janakpur train,
  and the Ariane 6 launch of 36 Amazon Leo satellites is scrubbed on
  the pad.
- **Also:** a scoreboard of six decided numbers (239/5, 720/9 dec,
  24,000 cr, 36, 51.7, +2.2%), a horizontal PMI bar chart for six
  economies, eighteen briefs in two columns, a "tonight, still to
  come" box (US flash PMIs, Fed's Williams, earnings after the close)
  and a date-check box naming stories that were NOT Monday (the
  killer-robot talks ended Saturday, the penny law was signed Friday,
  COP31 collapsed Sunday).
- **How it is built:** pure Python 3.13 standard library only — no Pillow,
  no network. A hand-built vector stroke font draws every letter; the
  program writes a deterministic 1024x1024 PNG to `/output/entry.png`
  (`MAKEFUN_OUTPUT_DIR` overrides the output directory for local runs).

Run it: `MAKEFUN_OUTPUT_DIR=out python3 main.py`

Entry for [news-image-20261123](https://make.fun/bounty/news-image-20261123)
on [make.fun](https://make.fun).
