#!/usr/bin/env python3
"""Cross-essay consistency checker for a whole application (e.g. Chevening's 4 essays).

Catches what single-essay review can't:
  1. The same story/passage reused across essays (holistic-review rule H3)
  2. Conflicting years/numbers for the same entity (e.g. "GYF … 2020" vs "GYF … 2022")
  3. Same quantity noun with different numbers ("3,000 students" vs "1,000 students")
  4. Claims that contradict the facts ledger (applicant/facts.yaml), and numbers not in it
  5. Word counts against program limits
  6. Story allocation matrix: which entities appear in which essay

Usage:
    python check_consistency.py essays/*.txt [--facts applicant/facts.yaml] [--program chevening] [--json]
Essay labels come from file names (leadership.txt -> "leadership"); name files after the
program's essay keys so per-essay limits apply.
"""
import argparse
import itertools
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ps_text import content_tokens, load_text, shingles, split_sentences, utf8_stdout, word_count  # noqa: E402
from check_draft import program_limit  # noqa: E402

YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
ACRONYM = re.compile(r"\b[A-Z][A-Z0-9]{1,}[a-z]?\b")
PROPER = re.compile(r"\b[A-Z][a-z]+(?:\s+(?:of\s+|for\s+|the\s+)?[A-Z][a-zA-Z]+)+")
QTY = re.compile(r"\b(\d[\d,.]*)\s*(%|k\b|million|thousand)?\s+((?:[a-z]+[\s-]){0,1}[a-z]+)", re.I)
IGNORE = {"I", "UK", "US", "USA", "MA", "MSc", "BA", "PhD", "CV", "OK", "AI"}
QTY_SKIP = {"years", "year", "months", "month", "days", "day", "weeks", "week", "hours", "times", "of", "and", "to", "in"}


# ---------- minimal YAML for the facts ledger (no PyYAML dependency) ----------
def _scalar(v):
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        return [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
    v = v.strip("'\"")
    return v


def load_facts(path):
    try:
        import yaml  # type: ignore
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data.get("facts", data) if isinstance(data, dict) else data
    except ImportError:
        pass
    facts, cur = [], None
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.split(" #", 1)[0].rstrip()
            if not line.strip() or line.strip().startswith("#") or line.strip() == "facts:":
                continue
            m = re.match(r"^\s*-\s+(\w+):\s*(.*)$", line)
            if m:
                cur = {m.group(1): _scalar(m.group(2))}
                facts.append(cur)
                continue
            m = re.match(r"^\s+(\w+):\s*(.*)$", line)
            if m and cur is not None:
                cur[m.group(1)] = _scalar(m.group(2))
    return facts


def norm_num(s):
    return s.replace(",", "").rstrip(".")


def entities(sentence):
    ents = set(a for a in ACRONYM.findall(sentence) if a not in IGNORE)
    for m in PROPER.finditer(sentence):
        if m.start() == 0 and len(m.group(0).split()) < 2:
            continue
        ents.add(m.group(0))
    return ents


def analyse(essays, facts=None, program=None):
    report = {"essays": {}, "reused_passages": [], "entity_year_conflicts": [], "quantity_conflicts": [],
              "ledger_mismatches": [], "unverified_numbers": [], "matrix": {}}
    ent_years = defaultdict(lambda: defaultdict(set))   # entity -> year -> {essay}
    ent_where = defaultdict(set)                        # entity -> {essay}
    qty = defaultdict(lambda: defaultdict(set))         # (anchor, noun) -> number -> {essay}
    qty_ctx = defaultdict(list)                         # (anchor, noun) -> [(num, essay, sentence, entities)]
    ctx = {}

    for label, text in essays.items():
        info = {"words": word_count(text)}
        if program:
            lim, unit = program_limit(program, label)
            if lim:
                n = word_count(text) if unit == "words" else len(text.strip())
                info.update({"limit": lim, "unit": unit, "over": n > lim})
        report["essays"][label] = info
        for s in split_sentences(text):
            ents = entities(s)
            yrs = YEAR.findall(s)
            for e in ents:
                ent_where[e].add(label)
                for y in yrs:
                    ent_years[e][y].add(label)
                    ctx[(e, y, label)] = s[:160]
            for m in QTY.finditer(s):
                num, noun = norm_num(m.group(1)), m.group(3).lower().strip()
                if YEAR.fullmatch(num) or noun.split()[0] in QTY_SKIP:
                    continue
                before = content_tokens(s[:m.start()])
                anchor = before[-1] if before else ""
                key = (anchor, noun)
                val = num + (m.group(2) or "")
                qty[key][val].add(label)
                qty_ctx[key].append((val, label, s[:160], ents))

    # 1. reused passages
    sh = {k: shingles(v) for k, v in essays.items()}
    for a, b in itertools.combinations(essays, 2):
        common = sh[a] & sh[b]
        if len(common) >= 3:
            jac = len(common) / max(1, len(sh[a] | sh[b]))
            report["reused_passages"].append({"essays": [a, b], "shared_5grams": len(common),
                                              "jaccard": round(jac, 3), "examples": sorted(common)[:4]})

    # 2. entity-year conflicts (same entity, different years, in different essays)
    for e, by_year in ent_years.items():
        if len(by_year) > 1:
            essays_involved = set().union(*by_year.values())
            if len(essays_involved) > 1:
                report["entity_year_conflicts"].append({
                    "entity": e,
                    "years": {y: sorted(ls) for y, ls in sorted(by_year.items())},
                    "context": {f"{y}@{l}": ctx[(e, y, l)] for y, ls in by_year.items() for l in ls}})

    # 3. quantity conflicts
    for (anchor, noun), nums in qty.items():
        if len(nums) > 1 and len(set().union(*nums.values())) > 1:
            report["quantity_conflicts"].append({"noun": f"{anchor} … {noun}".strip(" …"),
                                                 "values": {n: sorted(ls) for n, ls in nums.items()}})

    # 4. ledger
    if facts:
        ledger_nums = set()
        for f in facts:
            for key in ("number", "date"):
                v = f.get(key)
                if v not in (None, ""):
                    ledger_nums.add(norm_num(str(v)))
            ent = str(f.get("entity", "")).strip()
            date = str(f.get("date", "")).strip()
            if ent and date and ent in ent_years:
                wrong = {y: sorted(ls) for y, ls in ent_years[ent].items() if y != date[:4]}
                if wrong:
                    report["ledger_mismatches"].append({"fact": f.get("id", ent), "entity": ent,
                                                        "ledger_date": date, "essays_say": wrong})
            num = str(f.get("number", "")).strip()
            noun = str(f.get("unit", "")).strip().lower()
            claim_toks = set(content_tokens(str(f.get("claim", ""))))
            if num and noun:
                wrong = defaultdict(set)
                for (anchor, n2), occ in qty_ctx.items():
                    if n2 != noun:
                        continue
                    for val, label, sent, ents in occ:
                        related = (ent and ent in ents) or (anchor and anchor in claim_toks)
                        if related and norm_num(val) != norm_num(num):
                            wrong[val].add(label)
                if wrong:
                    report["ledger_mismatches"].append({"fact": f.get("id", noun), "noun": noun, "ledger_number": num,
                                                        "essays_say": {k: sorted(v) for k, v in wrong.items()}})
        for label, text in essays.items():
            for n in re.findall(r"\b\d[\d,.]*\b", text):
                n2 = norm_num(n)
                if n2 and n2 not in ledger_nums and len(n2) > 1:
                    report["unverified_numbers"].append({"essay": label, "number": n})

    # 6. matrix of entities appearing in 2+ essays or important single ones
    for e, ls in sorted(ent_where.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        report["matrix"][e] = sorted(ls)
    return report


def render_md(r, labels):
    out = ["# check_consistency report", ""]
    out.append("## Essays")
    for k, v in r["essays"].items():
        lim = f" / {v['limit']} {v['unit']}" + (" **OVER**" if v.get("over") else "") if "limit" in v else ""
        out.append(f"- {k}: {v['words']} words{lim}")
    out.append("")
    out.append("## Reused passages (same story twice?, holistic review rule H3)")
    out += [f"- {x['essays'][0]} ↔ {x['essays'][1]}: {x['shared_5grams']} shared phrases (e.g. \"{x['examples'][0]}\")"
            for x in r["reused_passages"]] or ["- none"]
    out.append("")
    out.append("## Same entity, different years (verify, may be two events or a contradiction)")
    for c in r["entity_year_conflicts"]:
        out.append(f"- **{c['entity']}**: " + "; ".join(f"{y} in {', '.join(ls)}" for y, ls in c["years"].items()))
        for k, s in list(c["context"].items())[:3]:
            out.append(f"  - {k}: \"{s}\"")
    if not r["entity_year_conflicts"]:
        out.append("- none")
    out.append("")
    out.append("## Same quantity, different numbers")
    out += [f"- \"{q['noun']}\": " + "; ".join(f"{n} in {', '.join(ls)}" for n, ls in q["values"].items())
            for q in r["quantity_conflicts"]] or ["- none"]
    out.append("")
    if r["ledger_mismatches"] or r["unverified_numbers"]:
        out.append("## Facts ledger")
        for m in r["ledger_mismatches"]:
            out.append(f"- MISMATCH {m['fact']}: ledger {m.get('ledger_date') or m.get('ledger_number')}, essays say {m['essays_say']}")
        if r["unverified_numbers"]:
            seen = sorted({(u['essay'], u['number']) for u in r["unverified_numbers"]})
            out.append("- Numbers not in the ledger (add them or check them): " + ", ".join(f"{n} ({e})" for e, n in seen[:25]))
        out.append("")
    out.append("## Story allocation matrix (entities in 2+ essays)")
    shared = {e: ls for e, ls in r["matrix"].items() if len(ls) > 1}
    if shared:
        out.append("| Entity | " + " | ".join(labels) + " |")
        out.append("|---|" + "---|" * len(labels))
        for e, ls in list(shared.items())[:25]:
            out.append(f"| {e} | " + " | ".join("●" if l in ls else "" for l in labels) + " |")
    else:
        out.append("- no entity appears in more than one essay")
    return "\n".join(out)


def main():
    utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("essays", nargs="+")
    ap.add_argument("--facts")
    ap.add_argument("--program")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    essays = {os.path.splitext(os.path.basename(p))[0]: load_text(p) for p in a.essays}
    facts = load_facts(a.facts) if a.facts and os.path.exists(a.facts) else None
    r = analyse(essays, facts, a.program)
    print(json.dumps(r, ensure_ascii=False, indent=2) if a.json else render_md(r, list(essays)))


if __name__ == "__main__":
    main()
