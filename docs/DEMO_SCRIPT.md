# Demo Script

## 1. UMKM Owner

1. Log in as `umkm@mitrascore.demo`.
2. Open the UMKM dashboard.
3. Continue onboarding for Warung Ibu Sari.
4. Confirm consent is visible.
5. Review profile fields and evidence upload controls.
6. Run Instant Evidence Check.
7. Submit to analyst when eligible.

## 2. Field Agent

1. Log in as `fieldagent@mitrascore.demo`.
2. Open assisted cases.
3. Select Warung Ibu Sari.
4. Upload evidence with `AGENT_ASSISTED` or `AGENT_VERIFIED`.
5. Add observation note.
6. Confirm mock extraction runs.

## 3. Analyst

1. Log in as `analyst@mitrascore.demo`.
2. Open submitted cases.
3. Select Warung Ibu Sari.
4. Run DeepScore Review.
5. Review score around `PROMISING`, confidence `MEDIUM`, signals, red flags, data used, data not used, and audit trail.
6. Save a human decision such as `NEEDS_MORE_DATA`.

## Expected Demo Outcome

Warung Ibu Sari should score around 74/100, readiness band `PROMISING`, confidence `MEDIUM`, with suggested action to request two additional transaction proofs and verify financing purpose before final review.
