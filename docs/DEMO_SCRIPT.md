# Demo Script

## 1. UMKM Owner

1. Log in as `umkm@mitrascore.demo`.
2. Open the UMKM dashboard.
3. Confirm the workflow panel shows the current stage and owner next actions.
4. Continue onboarding for Warung Ibu Sari.
5. Confirm consent is visible.
6. Review profile fields and evidence upload controls.
7. Run Instant Evidence Check.
8. Submit to analyst when eligible.
9. After analyst decision, return to the owner dashboard and confirm reviewer notes plus follow-up actions are visible.

For a blank-start self-test, log in as `umkm2@mitrascore.demo` with password `Demo123!` and create the borrower profile from scratch.
If the owner needs assisted onboarding, click `Minta Bantuan Agen`; this creates a draft assisted case that appears in the Field Agent dashboard.

## 2. Field Agent

1. Log in as `fieldagent@mitrascore.demo`.
2. Open assisted cases.
3. Select Warung Ibu Sari.
4. Confirm the workflow panel shows the field-agent next actions.
5. Upload evidence with `AGENT_ASSISTED` or `AGENT_VERIFIED`.
6. Add observation note.
7. Confirm mock extraction runs.
8. Run Instant Evidence Check.
9. When eligible, click `Kirim ke Analis` to send the owner or agent response back to analyst.

## 3. Analyst

1. Log in as `analyst@mitrascore.demo`.
2. Open submitted cases.
3. Confirm the workflow panel shows the analyst next actions.
4. Select Warung Ibu Sari.
5. Run DeepScore Review.
6. Review score around `PROMISING`, confidence `MEDIUM`, signals, red flags, data used, data not used, and audit trail.
7. Save a human decision:
   - `NEEDS_MORE_DATA` to request more evidence and send the case back to owner/agent.
   - `RECOMMENDED_FOR_REVIEW` to move the case to final financing review.
   - `APPROVED_FOR_FINANCING` for final human approval.
   - `NOT_RECOMMENDED_AT_THIS_STAGE` or `DECLINED` when the case should not proceed.
8. Confirm the owner and field-agent dashboards show the reviewer decision, notes, and role-specific follow-up actions.

## Expected Demo Outcome

Warung Ibu Sari should score around 74/100, readiness band `PROMISING`, confidence `MEDIUM`, with suggested action to request two additional transaction proofs and verify financing purpose before final review. The case should move cleanly between owner, field agent, and analyst through visible workflow stages and audit logs.

## Reset Demo State

Before repeating a full demo from the initial state:

```bash
cd apps/api
. .venv/bin/activate
python manage.py reset_local_demo --yes
```

For Docker/Postgres, prefix the same command with `DATABASE_URL=postgres://mitrascore:mitrascore@localhost:5432/mitrascore`.
