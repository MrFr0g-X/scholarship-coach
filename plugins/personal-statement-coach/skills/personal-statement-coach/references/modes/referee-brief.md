# Mode: Referee brief

Recommendation letters work best when they **complement** the essays, adding evidence the essays don't contain, rather than repeating them. AI help is often acceptable for a recommendation-letter *draft*, because the referee reviews it, edits it and owns it. Still check the program's rules: some require referees to write independently.

## Inputs
- The program profile (criteria, number of referees).
- The applicant's essays and story bank.
- The referees: name, role, how they know the applicant, and for how long.

## Output, one brief per referee
```markdown
## Brief for <referee name, role>
**Program and criteria they should speak to:** <e.g. Gates: academic excellence + leadership>
**Why you (the referee) are the right person:** <relationship, duration, what you saw first-hand>
**2-3 specific examples only you can confirm** (not already central in my essays):
1. <story/fact id from facts.yaml>, what you observed, with numbers/dates
2. …
**Qualities to illustrate:** <1-2 qualities with the example that shows each>
**Comparisons, if you're comfortable:** <e.g. "top 5% of students I've supervised in 10 years">
**Practical:** deadline <date + source>, submission link, length, format/letterhead
```

## Optional draft letter (only when the user asks and the program allows it)
- Write it **in the referee's voice and perspective**, built only from facts in the brief, with `[REFEREE TO CONFIRM]` markers on every claim.
- Remind the user that the referee must review it, edit it and send it themselves.

## Allocation check
Make sure the referees together cover the program criteria without three letters saying the same thing. Show a small matrix: criteria × referees.
