import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "plugins", "personal-statement-coach", "skills", "personal-statement-coach", "scripts")
FIX = os.path.join(ROOT, "tests", "fixtures")
sys.path.insert(0, SCRIPTS)

import check_consistency  # noqa: E402
import check_draft  # noqa: E402
from ps_text import split_sentences, word_count  # noqa: E402


def read(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as f:
        return f.read()


def messages(res, section=None):
    return [f["message"] for f in res["findings"] if section is None or f["section"] == section]


# ---------- ps_text ----------
def test_sentence_split_and_count():
    assert split_sentences("I led 30 people. Then we won!") == ["I led 30 people.", "Then we won!"]
    assert word_count("Within six months, readmissions fell from 46 to 29.") == 9


# ---------- check_draft ----------
def test_weak_draft_raises_every_planted_flag():
    res = check_draft.analyse(read("weak_leadership_draft.txt"), limit=300)
    banned = " ".join(messages(res, "banned"))
    for rule in ["Feedback #7", "Feedback #9", "Feedback #17", "Feedback #11", "Feedback #10", "Rule G3"]:
        assert rule in banned, rule
    assert any("Room to add" in m for m in messages(res, "length"))
    assert any("One-sentence paragraph" in m for m in messages(res, "structure"))
    assert any("Vague quantities" in m for m in messages(res, "evidence"))
    assert any("too personal" in m for m in messages(res, "content"))
    assert messages(res, "passive")
    assert any("passionate about" in m for m in messages(res, "generic"))


def test_over_limit_and_chars_mode():
    text = "word " * 320
    assert any("OVER LIMIT" in m for m in messages(check_draft.analyse(text, limit=300)))
    res = check_draft.analyse("Short text here.", limit=10, unit="chars")
    assert any("OVER LIMIT" in m for m in messages(res, "length"))


def test_arabic_and_placeholders_flagged():
    res = check_draft.analyse("I trained 40 nurses in 2021 for my community. منحة\n\nI will return. [NUMBER?]")
    msgs = " ".join(messages(res, "content"))
    assert "Arabic script" in msgs
    assert "placeholder" in msgs


def test_clean_paragraph_has_no_banned_hits():
    text = ("In 2021, I noticed that 46 children a month came back to our ward. With two colleagues, I designed a "
            "picture-based sheet and trained 25 nurses. Within six months, readmissions fell to 29.\n\n"
            "Most importantly, I will take this to every ward in Assiut so more mothers and children benefit.")
    assert messages(check_draft.analyse(text), "banned") == []


def test_program_limit_from_profile():
    lim, unit = check_draft.program_limit("chevening", "leadership")
    assert lim == 300 and unit == "words"


def test_cli_json():
    out = subprocess.run([sys.executable, os.path.join(SCRIPTS, "check_draft.py"),
                          os.path.join(FIX, "weak_leadership_draft.txt"), "--limit", "300", "--json"],
                         capture_output=True, text=True, encoding="utf-8", check=True).stdout
    data = json.loads(out)
    assert data["stats"]["words"] == 168


# ---------- check_consistency ----------
def _app():
    essays = {n: read(f"app/{n}.txt") for n in ("leadership", "networking")}
    facts = check_consistency.load_facts(os.path.join(FIX, "app", "facts.yaml"))
    return check_consistency.analyse(essays, facts, "chevening")


def test_reused_story_detected():
    r = _app()
    assert r["reused_passages"] and set(r["reused_passages"][0]["essays"]) == {"leadership", "networking"}


def test_fellowship_year_conflict_detected():
    r = _app()
    gyf = [c for c in r["entity_year_conflicts"] if c["entity"] == "GYF"]
    assert gyf and set(gyf[0]["years"]) == {"2020", "2022"}


def test_quantity_conflict_detected_without_false_positive():
    r = _app()
    nouns = {q["noun"]: q["values"] for q in r["quantity_conflicts"]}
    assert "trained … students" in nouns
    assert set(nouns["trained … students"]) == {"3000", "1000"}
    # the workshop "100 students" and "30 fellows" must not be grouped with the reach figure
    assert not any("30" in v for v in nouns.values())


def test_ledger_mismatches():
    r = _app()
    ids = {m["fact"] for m in r["ledger_mismatches"]}
    assert {"gyf", "reach"} <= ids


def test_word_limits_from_program():
    r = _app()
    assert r["essays"]["leadership"]["limit"] == 300
    assert r["essays"]["leadership"]["over"] is False


def test_minimal_yaml_parser():
    facts = check_consistency.load_facts(os.path.join(FIX, "app", "facts.yaml"))
    assert facts[0]["id"] == "gyf" and str(facts[0]["date"]) == "2022"


# ---------- profile_init ----------
def test_profile_init_creates_and_never_overwrites(tmp_path):
    target = tmp_path / "applicant"
    script = os.path.join(SCRIPTS, "profile_init.py")
    subprocess.run([sys.executable, script, str(target)], check=True, capture_output=True)
    for name in ("profile.md", "story-bank.md", "facts.yaml", "voice.md", "tracker.md"):
        assert (target / name).exists()
    (target / "voice.md").write_text("mine", encoding="utf-8")
    subprocess.run([sys.executable, script, str(target)], check=True, capture_output=True)
    assert (target / "voice.md").read_text(encoding="utf-8") == "mine"
