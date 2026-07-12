# 🧰 Asset arsenal

A license-clean library of CC0 references and assets — HDRIs, textures, and 3D props — you can draw from for your renders. Start with the bundled `samples/`, then grow it with the fetcher.

- **Grow the library:** `node arsenal-fetch.cjs --hdris N --textures N --models N` — pulls more CC0 assets from [Poly Haven](https://polyhaven.com) into `samples/`.
- **What's actually here:** `00-INDEX.json` is the manifest — the `sources` list (where assets come from) plus an `assets[]` array of what's been pulled to disk. Nothing is "in the arsenal" until it's a real entry with a path.
- **Two kinds of haul:** STUDY references (learn from, never shipped) vs USABLE assets (license-clear — can go in a render). Every source tags its `license` and whether it's `usable`.

The binary contents can get large (GBs); keep them out of version control if you commit this kit — only this README and the manifest need tracking.
