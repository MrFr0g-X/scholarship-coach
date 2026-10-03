# Changelog

## 1.0.0, 2026-10-03
First public release as a Claude Code plugin.

### Added
- **Applicant memory:** `./applicant/` profile, story bank, facts ledger (`facts.yaml`), voice samples, tracker; `/ps-start` onboarding with CV/PDF import.
- **Program profiles** for 12 programs (Chevening, Fulbright, DAAD, Erasmus Mundus, Gates Cambridge, Rhodes, Commonwealth, MEXT, GKS, Türkiye Bursları, Stipendium Hungaricum, university SOP), with official sources and `last_checked` dates.
- **AI-policy matrix:** Chevening (prohibited), Rhodes (limited use, with disclosure), DAAD (allowed if declared).
- **`check_consistency.py`:** reused stories, conflicting years and numbers across essays, facts-ledger mismatches, story allocation matrix.
- **`check_draft.py` upgrades:** `--program/--essay` limits, character mode, `--json`, `.docx`/`.pdf` input, placeholder and paragraph-rhythm checks.
- **New modes:** Mock interview (scored per answer), Reframe, Profile, Referee brief, Elevator pitch, Consistency check.
- **8 slash commands:** `/ps-start`, `/ps-write`, `/ps-review`, `/ps-adapt`, `/ps-check`, `/ps-interview`, `/ps-reframe`, `/ps-pitch`.
- **Arabic-first guide:** dialect → intent mapping, program names in Arabic, cultural notes; Arabic README.
- **Calibration anchors** for review scoring; 16 eval cases; pytest suite.

### Changed
- Chevening guidance updated to current official criteria: the study in the UK essay focuses on the **first-choice course**, and the career plan needs **short, mid and long-term** goals plus UK collaboration.

## 0.2, personal version
Write, Coach, Plan, Review, Adapt, Tighten and Polish modes.
