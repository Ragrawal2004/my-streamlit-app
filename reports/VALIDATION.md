# Validation — agent vs. independent hand calculation

Each customer below was recomputed from raw Excel columns with plain arithmetic and compared with the agent. All assertions passed.

## CUST0007 — Travel → ON_TRACK / MAINTAIN

**Input:** income ₹1,84,955, expenses ₹1,34,200, investment ₹23,100, goal ₹2,03,313 in 18 months, impulse score 38. Actual outcome in dataset: **Yes**.

**Hand calculation:** surplus = ₹1,84,955 − ₹1,34,200 = ₹50,755; required = ₹2,03,313 ÷ 18 = ₹11,295; committed = min(investment, surplus) = ₹23,100; gap = ₹0; status = ON_TRACK.

**Agent recommendation:** Maintain the current ₹23,100 monthly investment.

**Agent explanation:** For the Travel goal of ₹2,03,313 over 18 months (1 yr 6 mo), the plan needs ₹11,295 a month. The ₹23,100 already invested each month covers the ₹11,295 required. Recommended next step: Maintain the current ₹23,100 monthly investment. It already covers the ₹11,295 required (205% coverage). Alternative: Optionally reach the goal in 5 months by directing the full ₹50,755 surplus to it. The ML model, trained on 1,000 customers, estimates a 96% likelihood of achievement for this profile.

**Check:** ✅ required, gap, status, months-to-goal and savings rate all match; explanation numbers match the calculation layer.

## CUST0001 — Retirement → AT_RISK / INCREASE_CONTRIBUTION

**Input:** income ₹1,68,230, expenses ₹76,600, investment ₹29,200, goal ₹53,98,537 in 165 months, impulse score 41. Actual outcome in dataset: **No**.

**Hand calculation:** surplus = ₹1,68,230 − ₹76,600 = ₹91,630; required = ₹53,98,537 ÷ 165 = ₹32,718; committed = min(investment, surplus) = ₹29,200; gap = ₹3,518; status = AT_RISK.

**Agent recommendation:** Increase the monthly goal contribution by ₹3,518 (to ₹32,718).

**Agent explanation:** For the Retirement goal of ₹53,98,537 over 165 months (13 yr 9 mo), the plan needs ₹32,718 a month. Current invested contribution (₹29,200) is ₹3,518 short of the ₹32,718 required, but the full monthly surplus (₹91,630) could cover it. Recommended next step: Increase the monthly goal contribution by ₹3,518 (to ₹32,718). This uses 6% of the ₹62,430 surplus that is currently not invested, so no spending cut is strictly required. Alternative: Keep the current contribution and extend the timeline to 185 months (15 yr 5 mo). The ML model, trained on 1,000 customers, estimates a 2% likelihood of achievement for this profile. Caution: although the gap is closable on paper, the ML model estimates only 2% likelihood of achievement for similar profiles in the dataset.

**Check:** ✅ required, gap, status, months-to-goal and savings rate all match; explanation numbers match the calculation layer.

## CUST0012 — Vehicle → NEEDS_ADJUSTMENT / REDUCE_EXPENSES

**Input:** income ₹51,186, expenses ₹33,700, investment ₹6,500, goal ₹7,09,336 in 40 months, impulse score 52. Actual outcome in dataset: **No**.

**Hand calculation:** surplus = ₹51,186 − ₹33,700 = ₹17,486; required = ₹7,09,336 ÷ 40 = ₹17,733; committed = min(investment, surplus) = ₹6,500; gap = ₹247; status = NEEDS_ADJUSTMENT.

**Agent recommendation:** Cut monthly expenses by ₹247 (0.7% of spending) and invest the full surplus.

**Agent explanation:** For the Vehicle goal of ₹7,09,336 over 40 months (3 yr 4 mo), the plan needs ₹17,733 a month. Even the entire monthly surplus (₹17,486) is ₹247 short of the ₹17,733 required, so the goal amount, timeline or spending must change. Recommended next step: Cut monthly expenses by ₹247 (0.7% of spending) and invest the full surplus. That exactly closes the shortfall within the original 40 months. It is well within a realistic cut: bringing the expense ratio down to the dataset median of 57.2% would free up to ₹4,401 a month. High impulse spending suggests discretionary spending is the place to start. Alternative: Keep the 40-month timeline with a smaller target of about ₹6,99,440. The ML model, trained on 1,000 customers, estimates a 14% likelihood of achievement for this profile.

**Check:** ✅ required, gap, status, months-to-goal and savings rate all match; explanation numbers match the calculation layer.

## CUST0014 — Travel → NEEDS_ADJUSTMENT / COMBINED

**Input:** income ₹23,226, expenses ₹16,700, investment ₹3,600, goal ₹2,63,483 in 12 months, impulse score 31. Actual outcome in dataset: **No**.

**Hand calculation:** surplus = ₹23,226 − ₹16,700 = ₹6,526; required = ₹2,63,483 ÷ 12 = ₹21,957; committed = min(investment, surplus) = ₹3,600; gap = ₹15,431; status = NEEDS_ADJUSTMENT.

**Agent recommendation:** Cut expenses by ₹3,405 (20%) and extend the timeline to 27 months (2 yr 3 mo).

**Agent explanation:** For the Travel goal of ₹2,63,483 over 12 months (1 yr), the plan needs ₹21,957 a month. Even the entire monthly surplus (₹6,526) is ₹15,431 short of the ₹21,957 required, so the goal amount, timeline or spending must change. Recommended next step: Cut expenses by ₹3,405 (20%) and extend the timeline to 27 months (2 yr 3 mo). A realistic expense cut alone does not close the ₹15,431 gap, so it is combined with a longer timeline. Alternative: Keep the 12-month timeline with a smaller target of about ₹78,312. The ML model, trained on 1,000 customers, estimates a 22% likelihood of achievement for this profile.

**Check:** ✅ required, gap, status, months-to-goal and savings rate all match; explanation numbers match the calculation layer.

## CUST0028 — Retirement → NEEDS_ADJUSTMENT / EXTEND_TIMELINE

**Input:** income ₹1,33,227, expenses ₹73,900, investment ₹3,300, goal ₹41,94,242 in 49 months, impulse score 27. Actual outcome in dataset: **No**.

**Hand calculation:** surplus = ₹1,33,227 − ₹73,900 = ₹59,327; required = ₹41,94,242 ÷ 49 = ₹85,597; committed = min(investment, surplus) = ₹3,300; gap = ₹26,270; status = NEEDS_ADJUSTMENT.

**Agent recommendation:** Extend the timeline to 71 months (5 yr 11 mo) while investing the full ₹59,327 surplus.

**Agent explanation:** For the Retirement goal of ₹41,94,242 over 49 months (4 yr 1 mo), the plan needs ₹85,597 a month. Even the entire monthly surplus (₹59,327) is ₹26,270 short of the ₹85,597 required, so the goal amount, timeline or spending must change. Recommended next step: Extend the timeline to 71 months (5 yr 11 mo) while investing the full ₹59,327 surplus. Expenses are already at or below the dataset median ratio, so a longer timeline is the main lever. Alternative: Keep the 49-month timeline with a smaller target of about ₹29,07,023. The ML model, trained on 1,000 customers, estimates a 3% likelihood of achievement for this profile.

**Check:** ✅ required, gap, status, months-to-goal and savings rate all match; explanation numbers match the calculation layer.
