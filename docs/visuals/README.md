# Dashboard Visuals

Place your Power BI dashboard screenshot here as `dashboard-preview.png`.

## Guidelines for the Mock Dashboard

Create a Power BI dashboard using the synthetic data from `examples/sample_output.csv` (or a larger generated dataset) that demonstrates:

1. **NPS Score Distribution** -- Histogram or bar chart showing Promoter/Passive/Detractor breakdown
2. **Sentiment Trend** -- Line or box plot showing sentiment scores over time (by quarter or month)
3. **Topic Frequency** -- Bar chart of most-mentioned topic categories
4. **Directional Topic Analysis** -- Stacked bar showing "is good" vs. "is bad" for each category (this is the highest-value visual)
5. **Regional Breakdown** -- Geographic or segment-based slicing

Use only synthetic/fictional data. No real customer names, account numbers, or feedback text.

## Recommended Layout

```
+-----------------------------------------------------+
|  NPS Score Distribution    |  Sentiment Trend (YoY)  |
|  [Donut/Bar Chart]         |  [Box Plot by Year]     |
+-----------------------------------------------------+
|  Topic Frequency           |  Good vs Bad by Topic   |
|  [Horizontal Bar]          |  [Stacked Bar]          |
+-----------------------------------------------------+
|  Filters: Region | Segment | Date Range             |
+-----------------------------------------------------+
```
