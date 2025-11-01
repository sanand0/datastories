multi_message / approx_1040
| stage            |   prompt_tokens |   cached_tokens | elapsed   |   messages |   local_estimate |
|------------------|-----------------|-----------------|-----------|------------|------------------|
| immediate_repeat |            1225 |            1152 | 2253 ms   |         13 |             1213 |
| warm             |            1225 |               0 | 1327 ms   |         13 |             1213 |

multi_message / approx_2048
| stage            |   prompt_tokens |   cached_tokens | elapsed   |   messages |   local_estimate |
|------------------|-----------------|-----------------|-----------|------------|------------------|
| immediate_repeat |            2235 |            2176 | 1389 ms   |         23 |             2213 |
| ttl_probe_1      |            2235 |            2176 | 1147 ms   |         23 |             2213 |
| ttl_probe_2      |            2235 |               0 | 1239 ms   |         23 |             2213 |
| ttl_probe_3      |            2235 |               0 | 1583 ms   |         23 |             2213 |
| warm             |            2235 |               0 | 1590 ms   |         23 |             2213 |

single_message / approx_1040
| stage            |   prompt_tokens |   cached_tokens | elapsed   |   messages |   local_estimate |
|------------------|-----------------|-----------------|-----------|------------|------------------|
| immediate_repeat |            1170 |            1024 | 1261 ms   |          2 |             1169 |
| warm             |            1170 |               0 | 1379 ms   |          2 |             1169 |

single_message / approx_2048
| stage            |   prompt_tokens |   cached_tokens | elapsed   |   messages |   local_estimate |
|------------------|-----------------|-----------------|-----------|------------|------------------|
| immediate_repeat |            2130 |               0 | 1125 ms   |          2 |             2129 |
| ttl_probe_1      |            2130 |            1024 | 1441 ms   |          2 |             2129 |
| ttl_probe_2      |            2130 |               0 | 2156 ms   |          2 |             2129 |
| ttl_probe_3      |            2130 |               0 | 1810 ms   |          2 |             2129 |
| warm             |            2130 |               0 | 1432 ms   |          2 |             2129 |