#!/usr/bin/env python3
"""Mechanical checks for one personal statement / motivation letter / essay.

Encodes the method's "don'ts" and feedback mistakes (references/method.md) plus
generic-prose patterns (references/voice-guide.md). Findings are leads for the
reviewer to verify, not verdicts.

Usage:
    python check_draft.py draft.txt [--limit 300] [--unit words|chars]
    python check_draft.py draft.docx --program chevening --essay leadership
    python check_draft.py draft.txt --json
    cat draft.txt | python check_draft.py - --limit 500
"""
import argparse
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ps_text import (ARABIC_RE, BANNED, BEYOND_SELF, CONNECTORS, GENERIC,  # noqa: E402
                     load_text, split_paragraphs, split_sentences, utf8_stdout, words)

PROGRAMS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "programs")


def program_limit(program, essay):
    """Read `essays:` / `default_limit:` / `unit:` from a program profile's front matter."""
    path = os.path.join(PROGRAMS_DIR, f"{program}.md")
    if not os.path.exists(path):
        return None, None
    meta = {}
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return None, None
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    unit = meta.get("unit", "words")
    if essay and "essays" in meta:
        for part in meta["essays"].split(";"):
            if "=" in part:
                k, v = part.split("=", 1)
                if k.strip() == essay and v.strip().isdigit():
                    return int(v.strip()), unit
    lim = meta.get("default_limit", "")
    return (int(lim) if lim.isdigit() else None), unit


def analyse(text, limit=None, unit="words"):
    paras = split_paragraphs(text)
    sents = split_sentences(text)
    wc, cc = len(words(text)), len(text.strip())
    low = text.lower()
    F = []  # findings: (section, message)

    def add(section, msg):
        F.append({"section": section, "message": msg})

    # Length & structure
    count = wc if unit == "words" else cc
    stats: dict = {"words": wc, "chars": cc, "paragraphs": len(paras), "sentences": len(sents)}
    if limit:
        pct = count / limit * 100
        stats.update({"limit": limit, "unit": unit, "used_pct": round(pct)})
        if count > limit:
            add("length", f"OVER LIMIT: {count}/{limit} {unit} ({pct:.0f}%)")
        elif pct < 85:
            add("length", f"Room to add: {count}/{limit} {unit} ({pct:.0f}%), unused space in a competitive essay")
    for p in paras:
        if len(paras) > 1 and len(split_sentences(p)) == 1:
            add("structure", f"One-sentence paragraph (Feedback #27): \"{p[:90]}…\"")
        if re.match(r"^\s*(\d+[.)]|[ivx]+[.)]|paragraph\s+\d)", p, re.I):
            add("structure", f"Numbered paragraph (Feedback #26): \"{p[:60]}…\"")
        if re.match(r"^[^.!]{5,120}\?", p):
            add("structure", f"Paragraph opens with a question, restating the prompt? (Feedback #25): \"{p[:80]}…\"")
    lens = [len(words(p)) for p in paras]
    if lens and max(lens) > 220:
        add("structure", f"Very long paragraph ({max(lens)} words), split it (Feedback #3)")
    if len(paras) == 1 and wc > 150:
        add("structure", "Single block of text, break into paragraphs with blank lines (Feedback #6)")
    if len(lens) >= 4:
        mean = sum(lens) / len(lens)
        if mean and max(abs(x - mean) for x in lens) / mean < 0.15:
            add("voice", "Paragraphs are all nearly the same length, vary them by content (voice-guide §3)")

    # Opening
    first = sents[0] if sents else ""
    stats["first_sentence"] = first[:200]
    if re.match(r"^[\"'“]", first):
        add("opening", "Opens with a quotation, debatable; rephrase into yourself (Feedback #2)")
    if re.match(r"^(to |dear )", first, re.I):
        add("opening", "Opens with an address / 'To the … scholarship' (Feedback #10), fine only in a job-letter format")

    # Banned phrases
    for pat, why in BANNED:
        for m in re.finditer(pat, low):
            s = max(0, m.start() - 40)
            add("banned", f"\"…{text[s:m.end() + 30].strip()}…\" → {why}")

    # I balance
    starts_i = [s for s in sents if re.match(r"^(I|I'm|I've|I'd|I'll)\b", s)]
    pct_i = len(starts_i) / max(1, len(sents)) * 100
    stats["sentences_starting_with_I_pct"] = round(pct_i)
    if pct_i > 40:
        add("i_balance", f"{len(starts_i)}/{len(sents)} sentences start with 'I' ({pct_i:.0f}%), vary the subject (Feedback #1)")
    if re.search(r"(^|\s)i(\s|'m|'ve|'d|'ll)", text):
        add("i_balance", "Lowercase 'i' found, must be capital I (Feedback #28)")
    if len(re.findall(r"\b(he|she|they) (is|was|has|founded|works)\b", low)) >= 3 and len(re.findall(r"\bi\b", low)) < 3:
        add("i_balance", "Reads like third person / bio, write in first person (Feedback #8)")

    # Evidence
    nums = re.findall(r"\b\d[\d,.]*\s?(?:%|k|m|million|thousand)?\b", text, re.I)
    years = re.findall(r"\b(?:19|20)\d{2}\b", text)
    stats.update({"numbers": len(nums), "years": len(years)})
    if len(nums) < 3:
        add("evidence", "Few numbers, add counts/dates/scale for credibility (numbers-and-dates lesson)")
    vague = re.findall(r"\b(many|a lot of|lots of|several|numerous|various|some)\b", low)
    if vague:
        add("evidence", f"Vague quantities ({len(vague)}): {', '.join(sorted(set(vague)))}, replace with numbers")

    # Voice
    passive = [s for s in sents if re.search(r"\b(was|were|is|are|been|being|be)\s+(\w+ly\s+)?\w+(ed|en)\b", s, re.I)]
    for s in passive[:6]:
        add("passive", f"Possibly passive (Don't D8; verify): \"{s[:140]}\"")
    for s in sents:
        if len(words(s)) > 40:
            add("voice", f"Long sentence ({len(words(s))} words), fails read-aloud test? \"{s[:100]}…\"")
    if len(sents) >= 6:
        sl = [len(words(s)) for s in sents]
        mean = sum(sl) / len(sl)
        sd = (sum((x - mean) ** 2 for x in sl) / len(sl)) ** 0.5
        stats.update({"sentence_len_mean": round(mean), "sentence_len_sd": round(sd)})
        if sd < 5:
            add("voice", f"Very uniform sentence rhythm (mean {mean:.0f}, spread {sd:.0f}), vary it")

    hits = [text[m.start():m.end()] for pat in GENERIC for m in re.finditer(pat, low)]
    if hits:
        add("generic", "Generic phrasing: " + ", ".join(f"\"{h}\"" for h in hits))
    conn = Counter(c for c in CONNECTORS for _ in re.finditer(r"\b" + c + r"\b", low))
    if sum(conn.values()) >= 3:
        add("generic", f"Connector chain {dict(conn)}, vary or cut")
    dashes = text.count(", ") + text.count(" - ")
    if dashes >= 3:
        add("generic", f"{dashes} dashes, use plainer punctuation")
    starters = Counter(" ".join(words(s)[:2]).lower() for s in sents if len(words(s)) >= 2)
    rep = [f"\"{k}\"×{v}" for k, v in starters.items() if v >= 3]
    if rep:
        add("generic", f"Repeated sentence openings: {', '.join(rep)}")

    # Content signals
    bs = len(re.findall(BEYOND_SELF, low))
    stats["beyond_self_words"] = bs
    if bs < 3:
        add("content", "Few beyond-self words, purpose may be self-centred (Part 1 item 1)")
    if paras and not re.search(BEYOND_SELF, paras[-1].lower()):
        add("content", "Final paragraph doesn't land on others/community ('Most importantly…' move)")
    if not re.search(r"\b(will|plan|goal|within|by 20\d\d|years?)\b", low):
        add("content", "No future-plan language found (Must-include M3)")
    if ARABIC_RE.search(text):
        add("content", "Arabic script found, never include Arabic in the essay (Feedback #12)")
    if re.search(r"\b(coffee shop|cafe|café|my fianc[eé]e?|beach|sahel|hang out with (my )?friends)\b", low):
        add("content", "Possibly too personal (Don't D2)")
    placeholders = re.findall(r"\[[^\]]{1,80}\]", text)
    if placeholders:
        add("content", f"{len(placeholders)} unfilled placeholder(s): {', '.join(placeholders[:6])}")

    return {"stats": stats, "findings": F}


SECTIONS = [("length", "Length"), ("structure", "Structure"), ("opening", "Opening (hook)"),
            ("banned", "Banned phrases & hedges"), ("i_balance", "'I' balance"), ("evidence", "Evidence"),
            ("passive", "Passive voice"), ("voice", "Voice & rhythm"), ("generic", "Generic phrasing"),
            ("content", "Content signals")]


def render_md(res):
    s = res["stats"]
    out = ["# check_draft report", ""]
    line = f"- {s['words']} words, {s['chars']} characters, {s['paragraphs']} paragraphs, {s['sentences']} sentences"
    if "limit" in s:
        line += f", limit {s['limit']} {s['unit']} ({s['used_pct']}% used)"
    out += [line, f"- First sentence: \"{s.get('first_sentence', '')}\"",
            f"- Sentences starting with 'I': {s['sentences_starting_with_I_pct']}% · numbers: {s['numbers']} · years: {s['years']} · beyond-self words: {s['beyond_self_words']}", ""]
    for key, title in SECTIONS:
        items = [f["message"] for f in res["findings"] if f["section"] == key]
        if items:
            out.append(f"## {title}")
            out += [f"- {m}" for m in items]
            out.append("")
    if not res["findings"]:
        out.append("No mechanical issues found. Now read it aloud and run the rubric.")
    return "\n".join(out)


def main():
    utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--unit", choices=["words", "chars"])
    ap.add_argument("--program", help="program profile id in references/programs (e.g. chevening)")
    ap.add_argument("--essay", help="essay key from the program profile (e.g. leadership)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    limit, unit = a.limit, a.unit
    if a.program:
        plim, punit = program_limit(a.program, a.essay)
        limit = limit or plim
        unit = unit or punit
    res = analyse(load_text(a.path), limit, unit or "words")
    print(json.dumps(res, ensure_ascii=False, indent=2) if a.json else render_md(res))


if __name__ == "__main__":
    main()
