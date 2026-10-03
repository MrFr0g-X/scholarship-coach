# Mode: Profile (/ps-start onboarding)

Build the applicant's memory **once**, so every later essay, review and interview reuses it. Everything stays local in `./applicant/`.

## Steps
1. **Create the folder:** `python <skill-dir>/scripts/profile_init.py` creates `./applicant/` (profile, story bank, facts ledger, voice, tracker, `drafts/`) and git-ignores it. It never overwrites existing files.
2. **Import what already exists.** Ask for a CV, LinkedIn PDF export or old essays.
   - Extract text: `python <skill-dir>/scripts/read_doc.py <file> --out applicant/cv.txt` (handles .docx, .pdf, .txt).
   - From it, fill `profile.md` basics and draft `facts.yaml` entries: every number, date, title, organisation and award, with `proof: CV` and a `TODO verify` note when unclear.
   - Draft story-bank stubs for the 3-6 strongest experiences, with STAR fields filled where the CV supports them and gaps under **Missing**.
3. **Capture the voice.** Ask for a writing sample, or two casual answers in their own words (Arabic or dialect is fine), and save them to `voice.md` with the coach's notes (vocabulary level, rhythm, phrases).
4. **Ask only for the gaps.** Use one round of 5-8 questions from `question-bank.md`: purpose beyond self, the 5-year vision, the belief line, challenges, and target programs.
5. **Set up the tracker.** For each target program, read its profile, list the essays and limits, and **look up deadlines live** with source URL and date checked. If you can't browse, leave them blank with "check portal".
6. **Summarise:** what's in the profile, what's missing, and the suggested next step (usually Plan for the first essay).

## Keeping it current
- **Coach, Reframe and Interview:** when a new story or fact surfaces, add it (ask first if it changes an existing fact).
- **Write:** after a draft is accepted, update `used_in` for each story and fact it uses.
- **Before submission:** run `check_consistency.py applicant/drafts/*.txt --facts applicant/facts.yaml --program <id>`.

## Privacy
Never upload or paste the profile anywhere outside the user's machine. Remind the user once that `applicant/` is git-ignored, so they shouldn't commit it to a public repo.
