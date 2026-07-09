# Music Store Database

## 1. Segmentation Logic and Justification

Segmentation blends **spend, frequency, and diversity** rather than spend
alone, so a customer who buys often across many genres outranks a one-time
big spender:

| Segment  | Rule |
|----------|------|
| Platinum | total_spent ≥ 40 **and** total_invoices ≥ 7 **and** unique_genres ≥ 5 |
| Gold     | total_spent ≥ 25 **and** total_invoices ≥ 5 |
| Silver   | total_spent ≥ 10 **and** total_invoices ≥ 2 |
| Bronze   | everything else |

**Why this strategy:** Platinum requires all three conditions (spend +
frequency + variety) because these are the customers worth prioritizing for
retention — high spend alone doesn't guarantee loyalty. Gold relaxes the
diversity requirement: they're high spenders/repeat buyers even if narrowly
focused on a few genres, so they're still valuable, just less "sticky."
Silver captures modestly engaged, repeat customers who could grow into Gold.
Bronze is the acquisition/reactivation pool — low signal either way.

## 2. Country Ranking Methodology

```
score = revenue*0.40 + customers*0.20 + avg_customer_revenue*0.15
      + avg_invoice*0.10 + genres*0.10 + customer_diversity*0.05
```

| Metric | Weight | Why |
|---|---|---|
| Total revenue | 0.40 | The direct business outcome,i.e., highest weight. |
| Customer count | 0.20 | Rewards market size, not just a few big spenders. |
| Avg revenue/customer | 0.15 | Rewards customer quality/value, not just volume. |
| Avg invoice value | 0.10 | Signals healthy per-transaction spend. |
| Genre diversity | 0.10 | A market buying across many genres is more resilient than one dependent on a single trend. |
| Customer diversity (unique artists) | 0.05 | Minor tiebreaker for catalog engagement depth. |

Countries are ranked with `RANK()` so ties share a position, and the top 3
by score are recommended for expansion.

## 3. Marketing Recommendation Strategy

Each customer's favorite genre is found with `ROW_NUMBER()` partitioned by
customer, ordered by purchase count — the single genre with the most
purchases wins ties by SQL's default row order, which is acceptable here
since we only need one representative genre per customer, not an exact tie
policy.

Campaigns are assigned **by segment**, not by genre, because segment
reflects overall value/engagement while genre only says *what* they buy:

| Segment | Campaign | Reasoning |
|---|---|---|
| Platinum | Early access to new releases | Reward loyalty, deepen retention — these customers are the least price-sensitive. |
| Gold | Album bundle discounts | Encourage a step up in basket size from already-frequent buyers. |
| Silver | Genre-based promotions | Use their proven genre affinity to convert them into more frequent buyers. |
| Bronze | First purchase coupon | Low commitment, low-cost incentive to establish a first real purchase pattern. |

The favorite genre is still surfaced per customer in the output so a
marketing team can personalize the campaign copy/content even though the
campaign *tier* is segment-driven.

## 4. Actionable Recommendations

1. **Prioritize retention spend on Platinum customers.** They're a small
   group but the segmentation criteria mean they're disproportionately
   valuable — an early-access program costs little and protects a revenue
   base that's expensive to replace.
2. **Run genre-targeted campaigns for Silver customers specifically.**
   They already show repeat behavior; a genre-based promo is the cheapest
   lever to convert them into Gold.
3. **Expand marketing/localization budget toward the top 3 ranked
   countries** identified by the performance score, since they combine high
   revenue *and* healthy customer counts, not just a couple of big spenders.
4. **Address genre concentration risk** in countries with high revenue but
   low genre diversity — a market reliant on 1-2 genres is more exposed to
   taste shifts; consider genre-expansion promotions there.
5. **Feature the top-selling artist and album** in front-of-store /
   homepage placement in the top-ranked countries — proven demand there is
   the lowest-risk way to lift average invoice value.
6. **Investigate the Bronze segment for reactivation**, since first-purchase
   coupons are cheap, but customers who never convert past one segment tier
   after a few offers likely need a different channel or price point.

## 5. Challenges Faced and How They Were Solved

- **CTE scope across statements.** The original draft tried to reuse CTEs
  like `customer_segments` and `country_rankings` in queries *after* a prior
  `SELECT ... ;` had already run. In standard SQL, a `WITH` clause only
  exists for the one statement it's attached to — once that statement's
  semicolon closes, the CTE is gone. Running the later queries as written
  would fail with "relation does not exist."
  **Fix:** either re-declare the needed CTEs at the top of each subsequent
  query, or fold every CTE into a single `WITH` clause
  ending in one final query. Both preserve the
  exact same calculation logic — nothing was recalculated differently, only
  re-scoped.
- **Combining heterogeneous report sections into one final dashboard
  (bonus).** The nine executive-report metrics have completely different
  column shapes (e.g. "top employee" vs "revenue by country"). A single
  `UNION ALL` requires matching column counts/types across all branches.
  **Fix:** standardized every branch to a common `(sort_order,
  report_section, dimension_1, dimension_2, metric_1, metric_2)` shape,
  casting numeric values to `text` so they align, then sorted the combined
  result by `sort_order` to preserve a logical report order.
- **Avoiding duplicate/inflated averages in `country_metrics`.** Because the
  underlying join fans out to one row per invoice line, aggregating
  straight from that join would inflate `avg_invoice_value`. **Fix:**
  `avg_invoice_value` is calculated once inside `customer_profile` (grouped
  to the customer level) and only averaged *again* at the country level in
  `country_metrics`, rather than being recomputed from the raw joined rows.
