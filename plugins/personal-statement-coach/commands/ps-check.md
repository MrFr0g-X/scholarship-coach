---
description: "Final consistency check across all your essays + facts ledger"
argument-hint: "[program] [files…]"
---

Use the personal-statement-coach skill in **Consistency check mode**.

Arguments: $ARGUMENTS

If no files are given, use `applicant/drafts/*`. Run `check_consistency.py` with `--facts applicant/facts.yaml` and `--program` when known, then `check_draft.py` on each essay. Explain each real issue (reused stories, conflicting dates/numbers, ledger mismatches, limits) and dismiss false positives.
