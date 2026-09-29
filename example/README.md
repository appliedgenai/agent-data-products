# Reproduce the synthetic metric example

From the paper's directory, run:

```text
python example/verify_metric.py
```

Requires Python 3.10 or newer; no external packages are needed. The script prints the July/August comparison and runs 17 contract and arithmetic tests. It returns a nonzero exit status if a test fails.

Expected totals: July 90/100 (90%); August 80/100 (80%); August recalculated with July's regional weights: 90%. Regional rates remain 95% and 70%. A deliberately incorrect shipment join changes the order denominators.

The records are synthetic. Frozen, certified order-level inputs are assumed. This demonstrates selected calculations and failure cases; it does not implement a production agent, permission system, historical replay, late-restatement process or full shipment certification. Fixed-offset timezone tests do not exercise daylight-saving changes.

See [the paper](../README.md) for the architecture and business interpretation, and [source notes](../SOURCES.md) for research scope.
