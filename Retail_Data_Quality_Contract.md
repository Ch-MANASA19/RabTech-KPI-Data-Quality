# Data Quality Contract — Retail Orders

**Version:** 1.0  
**Dataset:** RabTech Academy raw retail orders starter dataset  
**Decision owner:** Retail Operations Manager  
**Data owner:** Data Product Owner / Data Engineering  
**Analytics owner:** Data Analyst  
**Intended use:** Daily retail operations reporting and KPI calculations.

## 1. Agreement
The dataset may be used for decision-making only when the critical checks below pass or a named owner has explicitly accepted a documented exception. Raw source rows must be preserved. Failed rows should be quarantined for investigation, not silently deleted.

## 2. Data dimensions, thresholds, and actions

| Dimension / check | Acceptance threshold | Severity | Failure action |
|---|---:|---|---|
| Completeness: order ID | At least 99% nonblank | High | Quarantine rows missing order ID; alert Data Owner; block order-count KPI if threshold is breached. |
| Completeness: order date | At least 99% nonblank and parseable | High | Quarantine invalid dates; alert Data Engineering; block time-based KPIs if breached. |
| Completeness: quantity | At least 99% nonblank | High | Quarantine affected rows; block units-sold and sales calculations if breached. |
| Uniqueness: candidate order-line key | Duplicate rate ≤ 0.5% | High | Investigate repeated key; do not auto-delete until line-item semantics are confirmed. |
| Validity: quantity | At least 99.5% numeric and positive | High | Quarantine invalid rows; check whether negative values represent returns and document the rule. |
| Validity: unit price | At least 99.5% numeric and non-negative | High | Quarantine invalid rows; notify source-system owner. |
| Validity: order date | At least 99.5% parseable | High | Confirm date format/locale; block date-based KPIs if breached. |
| Consistency: sales ≈ quantity × unit price | Mismatch rate ≤ 1% among comparable rows | Medium | Investigate discount, tax, currency, and rounding rules; do not overwrite totals without source evidence. |
| Consistency: order date not in future | Future-dated rows ≤ 0.1% | Medium | Check source clock/timezone and parsing; correct from source evidence only. |
| Freshness: latest order date | No more than 3 days old for a daily production feed | High | Alert Data Engineering and Retail Operations; mark dashboard stale. Static historical starter files may fail this check by design. |

## 3. Refresh and service expectations
- Production refresh target: daily by 09:00 local time.
- Data freshness SLA: latest available business date no older than 3 calendar days.
- KPI dictionary and contract reviewed monthly, and whenever source columns or business definitions change.
- The notebook records a run-time profile and writes `data_quality_results.csv` and `data_profile_summary.csv`.

## 4. Escalation path
1. **Analyst** runs the notebook and attaches output files to the incident.
2. **Data Owner / Data Engineering** acknowledges High-severity failures within 1 business day and investigates the source.
3. **Retail Operations Manager** is notified if a critical KPI is blocked or the dashboard is stale.
4. If unresolved after 2 business days, escalate to the data platform lead / program supervisor.
5. Publish a known-issues note and label affected KPIs “provisional” until resolved.

## 5. KPI use controls
- Gross sales and net sales must not be treated as interchangeable.
- Net sales and cancellation rate require a trustworthy order-status field and a documented status mapping.
- Average order value is sales divided by distinct eligible orders, not by order lines.
- Negative quantities may represent returns in some systems; the notebook flags them for review rather than assuming they are always erroneous.
- If a required field is absent, mark the relevant KPI “not computable” rather than inventing a value.

## 6. Sign-off
- Decision owner: Retail Operations Manager — pending review
- Data owner: Data Product Owner / Data Engineering — pending review
- Analytics owner: Data Analyst — prepared for Task 2 submission
