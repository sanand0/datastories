# IMF WEO GDP forecast-error visualization

- Data source: [IMF Data WEO site](https://data.imf.org/en/datasets/IMF.RES%3AWEO)
- [Data viz](https://chatgpt.com/share/6a389d6e-4180-83e8-a759-95734a64b000) <!-- https://chatgpt.com/c/6a3863f4-6798-83ee-ae5c-6d17ee525ce6 -->
- [Analysis](https://chatgpt.com/share/6a389d9d-c7d4-83ee-b73c-d29b16c45781) <!-- https://chatgpt.com/c/6a387079-6dc0-83ee-ac9e-df650426ddd1 -->
  <!-- Ideation: https://claude.ai/chat/0943a775-b971-41f5-b578-3bf9319642a6 -->

Run locally:

```bash
python -m http.server 8000
# Open http://localhost:8000/
```

Do not open `index.html` directly from `file://`, because browsers usually block `fetch("data.json")` from local files.

Permalinks:

- `#country=India`
- `#metric=median`
- `#country=India&metric=median`

Compact `data.json` schema:

- `p`: forecast points as `[entityId, targetYear, horizon, forecastPct, actualPct, errorPp, vintageId, xNorm, jitter]`
- `e`: entity names
- `v`: vintage labels
- `g`: global stats rows `[horizon, n, mean, median, mae, optimisticShare]`
- `s`: per-entity stats using the same row schema
- `x`: example button definitions
