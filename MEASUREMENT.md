# Measurement plan

## Baseline

Recorded at `2026-08-01T15:47Z`, immediately before repository preparation, via a direct
anonymous request to the public Apify API:

```text
https://api.apify.com/v2/acts/rook-data-tools~new-food-service-license-leads
```

| Metric | Baseline |
|---|---:|
| Public / isPublic | true |
| Total builds | 2 |
| Total runs | 2 |
| Total users | 2 |
| Users, prior 7 days | 1 |
| Users, prior 30 days | 1 |
| Users, prior 90 days | 1 |
| Public runs, prior 30 days | 1 |
| Successful public runs, prior 30 days | 1 |
| Reviews | 0 |
| Rating | 0 |
| Bookmarks | 0 |

Pricing observed at the same endpoint (`pricingModel: PAY_PER_EVENT`):

- `actor-start`: $0.005, charged once per run start.
- `lead`: $0.005 per saved food-service license lead (the primary billed event).

`totalUsers`/`totalUsers30Days` are not reliable evidence of independent outside demand —
both actors created the same day as this one show the same ambiguity, and owner runs may
or may not be excluded from that counter. Report these numbers as a dated baseline only,
never as proof that outside buyers are already using the actor.

## Tagged outbound link

The README uses:

```text
https://apify.com/rook-data-tools/new-food-service-license-leads?utm_source=github&utm_medium=referral&utm_campaign=chicago_food_service_license_data_guide
```

The parameters describe the intended referral source. They are not evidence that Apify
provides UTM-level reporting, and this repository does not claim access to referral
analytics.

## Future checks

At 7, 30, and 90 days after publication:

1. Fetch the actor endpoint above and record the same fields in the baseline table.
2. In GitHub's repository Insights, record unique visitors, views, referring sites, and
   clones for the periods GitHub makes available. These owner-only traffic figures are
   not available from the anonymous repository API.
3. Record public GitHub stars and forks from:

   ```text
   https://api.github.com/repos/willowridge1234/chicago-food-service-license-data-guide
   ```

4. Compare deltas without claiming causation. Actor usage can change for reasons
   unrelated to this repository. Attribute traffic only when an actual referrer/campaign
   report supports it.

Do not backfill or estimate unavailable analytics.
