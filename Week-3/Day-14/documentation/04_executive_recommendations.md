## Task 6 — Executive Recommendations

### Business Opportunities

1. **Convert Bronze customers into higher tiers.** Over 95% of customers fall into the Bronze segment (Visualization 4), with very few reaching Silver, Gold, or Platinum. This is a large, largely untapped base — even a modest conversion rate through loyalty offers or re-engagement campaigns could meaningfully shift total customer lifetime value.

2. **Replicate Southwest's territory performance elsewhere.** Southwest generates ~$24M in revenue, nearly 5x Germany's ~$5M (Visualization 3), with Canada and Northwest forming a strong second tier (~$16M each). Understanding what drives Southwest's outperformance — team size, pricing, local demand — could inform investment in underperforming European territories like Germany and France.

3. **Double down on the Mountain-200 line, but manage its risk.** Six of the top 10 products by revenue are Mountain-200 variants, each generating $3.3M–$4.2M (Visualization 6). This is a clear opportunity for continued marketing and inventory prioritization, provided supply can keep pace with demand.

4. **Grow underperforming categories.** `category_performance` (Visualization 5) shows Bikes generating roughly 8x more revenue than the next-largest category, Components, with Accessories and Clothing contributing comparatively little — room for growth through bundling or repricing.

5. **Prevent stockouts on fast movers.** Only 0.5% of products are flagged "Low Stock" (Visualization 8), so overall inventory health is strong — but since Mountain-200 products dominate revenue, it's worth confirming none of the low-stock items overlap with top sellers.

### Business Risks

1. **Revenue is heavily concentrated in one product line.** Six of the top 10 revenue-generating products are Mountain-200 variants (Visualization 6). A slowdown in demand for this single line — due to competition, seasonality, or a supply issue — would disproportionately impact total revenue.

2. **Territory performance is unevenly distributed.** Southwest alone generates ~$24M vs. Germany's ~$5M (Visualization 3), meaning a small number of territories likely account for the majority of revenue. Overreliance on top territories leaves the business exposed if regional conditions shift.

3. **Sales performance is concentrated among a few top employees.** The top 3 salespeople (Linda Mitchell, Jillian Carson, Michael Blythe) each generate $9M–$10.2M, while the #10-ranked employee generates less than half that (Visualization 7). Heavy dependence on a small group of top performers creates vulnerability if any of them leave.

4. **Month-over-month revenue is highly volatile.** Growth swings from roughly +290% to −100% across the observed period (Visualization 2), rather than trending smoothly. This suggests sales are driven by irregular large orders rather than consistent demand, making forecasting and planning harder.

5. **Customer base is overwhelmingly low-tier.** With 95%+ of customers in the Bronze segment (Visualization 4), the business may be more dependent than it realizes on a small number of higher-value customers for a disproportionate share of revenue — a concentration risk if any of them churn.

### Actionable Recommendations

1. **Launch a tiered loyalty/re-engagement campaign** targeting Bronze customers to migrate a portion of the 95%+ base toward Silver/Gold, using `customer_segments` to identify near-threshold accounts.

2. **Investigate and replicate Southwest's success factors** (pricing, staffing, marketing mix) and pilot them in Germany and France, the two lowest-revenue territories.

3. **Protect Mountain-200 supply chain continuity** — monitor `inventory_metrics` specifically for this product line given its outsized share of revenue, and consider diversifying marketing spend toward Road-series products to reduce reliance on one line.

4. **Formalize a mentorship or best-practice program** pairing top performers (Linda Mitchell, Jillian Carson, Michael Blythe) with lower-ranked employees, using `employee_rankings` to identify coaching pairs.

5. **Exclude partial/incomplete months from growth reporting** — the sharp final-month drop in `sales_growth` (Visualization 2) likely reflects incomplete data rather than an actual decline, and should be flagged before drawing conclusions about business momentum.
