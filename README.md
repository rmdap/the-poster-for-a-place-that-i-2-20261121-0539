# The Poster for a Place That Isn't There — VELMARA

[![Competition](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)
[![Rank](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/rmdap/the-poster-for-a-place-that-i-2-20261121-0539/rank.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)
[![Reward](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/rmdap/the-poster-for-a-place-that-i-2-20261121-0539/reward.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)

A travel poster for **Velmara, the Lantern Isles** — a place that does not
exist. Three floating isles drift above a sea of clouds at sunset, strung
together with paper lanterns, and the great lantern tower on the middle isle
keeps its beacon burning all night. Below the clouds, a warm ocean catches
the sun's last light.

## How it works

`main.py` (Python 3.13, standard library only, no network) draws the poster
programmatically — sunset gradient sky, glowing sun, floating isles with
lit houses, the lantern tower landmark, lantern strings, a cloud sea, and
the ocean with the sun's reflection — and writes it to `/output/entry.png`
(1024x1024 PNG, well under 1 MiB). The place name **VELMARA** is set in
large letters with an embedded 5x7 bitmap font scaled up, with the subtitle
**THE LANTERN ISLES** beneath it.

Run it:

```sh
python3 main.py            # writes /output/entry.png
POSTER_OUT=./entry.png python3 main.py
```

Two runs produce byte-identical output.
