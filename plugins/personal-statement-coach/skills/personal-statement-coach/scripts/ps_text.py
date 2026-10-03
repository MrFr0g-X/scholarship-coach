"""Shared text helpers and rule lists for the personal-statement-coach scripts.

Rule tags in reasons (Feedback #N, Don't DN, Rule GN) refer to references/method.md.
"""
import re
import sys

ARABIC_RE = re.compile(r"[؀-ۿ]")

# (pattern, reason), matched case-insensitively against the lowercased text
BANNED = [
    (r"\bthank you\b|\bthanks for\b", "No 'thank you' anywhere (Feedback #7)"),
    (r"\bbest regards\b|\bkind regards\b|\byours sincerely\b|\bsincerely,", "No sign-off in a PS (Feedback #18); fine only in a job letter"),
    (r"looking forward to hearing", "Don't end with 'looking forward to hearing from you' (Feedback #9)"),
    (r"\bmy name is\b", "Don't start with your name (Feedback #17)"),
    (r"i hope you (like|enjoy)", "Don't write 'I hope you like this' (Feedback #20)"),
    (r"all (of )?this makes me (an? )?(excellent|ideal|perfect|good|great) candidate", "Don't declare yourself an excellent candidate (Feedback #11)"),
    (r"\bi am writing (this|to)\b|\bi'm writing (this|to)\b", "Don't open with 'I am writing to…' (Feedback #10)"),
    (r"\bi'?m not sure\b|\bi am not sure\b", "Hedging kills confidence (Rule G3)"),
    (r"\bprobably\b|\bhopefully\b|\bmaybe\b|\bperhaps\b", "Hedge word, state it confidently (Rule G3)"),
    (r"\bunfortunately\b", "Negative framing, use 'despite X, I did Y' (Rule G3)"),
    (r"\bparagraph (one|two|three|four|five|1|2|3|4|5)\b", "Don't number paragraphs (Feedback #26)"),
    (r"\bis defined as\b|\baccording to (the )?(oxford|cambridge|merriam)", "Definition opening, debatable, usually weak (Don't D5)"),
]

GENERIC = [
    r"since (my )?(early )?childhood", r"ever since i was (a child|young|little)", r"from a young age",
    r"passionate about", r"in today'?s (fast[- ]paced|modern|ever[- ]changing) world", r"in conclusion",
    r"\bdelve\b", r"\btapestry\b", r"testament to", r"\bpivotal\b", r"\bmultifaceted\b", r"\brealm\b",
    r"navigat(e|ing) the complexities", r"\bfoster(ing)?\b", r"\bleverag(e|ing)\b", r"\bunwavering\b",
    r"\bprofound(ly)?\b", r"embark(ed)? on (a|this|my) journey", r"ever[- ]evolving", r"\blandscape\b",
    r"not only .{1,60} but also", r"this experience taught me", r"i have always (been|wanted)",
    r"world[- ]class", r"\bprestigious\b", r"\bdream come true\b", r"\bhighlighting the importance\b",
    r"\bshowcas(e|ing)\b", r"\bplays? a (crucial|vital|key) role\b", r"\bcutting[- ]edge\b",
    r"\bwide (range|variety) of\b", r"\bnumerous\b", r"\bvarious\b",
]

CONNECTORS = ["furthermore", "moreover", "additionally", "in addition"]

BEYOND_SELF = r"\b(community|communities|society|others|people|country|region|youth|young|women|children|students|marginali[sz]ed|sdg|sustainab\w*|empower\w*)\b"

STOPWORDS = set("""a an the and or but if of to in on at by for with from as is are was were be been being
i me my we our you your he she they them their it its this that these those who which what when where why how
not no so than then also very just into over about after before during while within without up down out
have has had do does did will would can could should may might must shall am
more less over around about approximately nearly almost roughly some total than""".split())


def utf8_stdout():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]


def split_paragraphs(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]


def split_sentences(text):
    flat = re.sub(r"\s+", " ", text.strip())
    if not flat:
        return []
    parts = re.split(r"(?<=[.!?])\s+(?=[\"'“A-Z0-9])", flat)
    return [s.strip() for s in parts if s.strip()]


def words(text):
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9'’\-]*", text)


def word_count(text):
    return len(words(text))


def content_tokens(text):
    """Lowercased non-stopword tokens, for overlap detection."""
    return [w.lower() for w in words(text) if w.lower() not in STOPWORDS and len(w) > 2]


def shingles(text, n=5):
    toks = content_tokens(text)
    return {" ".join(toks[i:i + n]) for i in range(max(0, len(toks) - n + 1))}


def load_text(path):
    """Read .txt/.md directly; delegate .docx/.pdf to read_doc."""
    if path == "-":
        return sys.stdin.read()
    low = path.lower()
    if low.endswith((".docx", ".pdf")):
        from read_doc import read_document  # local module
        return read_document(path)
    with open(path, encoding="utf-8") as f:
        return f.read()
