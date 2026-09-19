# FootprintAI — 24-Hour Implementation Plan (Beginner Edition)

Goal: a working demo where you upload a consented photo, type a name, and see a graph of verified/unverified accounts with confidence scores, evidence, and a timeline.

---

## 0. The golden rules (read first)

1. **Get an ugly end-to-end version working by hour 12.** Polish later.
2. **Build the mock data layer first.** If the internet or an API dies during judging, you still demo.
3. **Build one small file at a time and test it alone** before connecting anything.
4. **Face recognition is the risky part.** Do it *after* text matching works.
5. **Test only on consenting people** (your team) and fake/synthetic personas.

---

## 1. Who does what (team of 4; adapt if 3)

| Person | Owns | Files |
|---|---|---|
| A - "Data" | GitHub + search discovery, mock data | `osint_fetcher.py`, `mock_data.json` |
| B - "AI Text" | Bio similarity, extraction, name fuzzy match | `bio_matcher.py`, `extractor.py` |
| C - "AI Face + Scoring" | Face embeddings, resolver | `face_matcher.py`, `resolver.py` |
| D - "UI + Docs" | Streamlit app, graph, timeline, README, demo | `app.py`, `graph_builder.py` |

With 3 people: merge A and B.

---

## 2. Setup (Hour 0–1, everyone)

### 2.1 Install
```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install streamlit streamlit-agraph sentence-transformers scikit-learn \
            requests python-dotenv rapidfuzz opencv-python-headless \
            numpy insightface onnxruntime
```
**If `insightface` fails to install** (common on Windows): use `pip install deepface` instead and adapt `face_matcher.py` (shown below). Do not lose more than 30 minutes on this.

### 2.2 Accounts and keys (free)
* **GitHub token:** GitHub → Settings → Developer settings → Personal access tokens → generate (no special scopes needed).
* **Search API:** SerpAPI free tier is small (~100 searches/month). **Use it sparingly and cache every result.** Alternative: the `duckduckgo-search` Python package needs no key.

### 2.3 Folder structure
```
footprintai/
├── app.py
├── bio_matcher.py
├── face_matcher.py
├── osint_fetcher.py
├── extractor.py
├── resolver.py
├── graph_builder.py
├── mock_data.json
├── cache/                 # saved API results
├── requirements.txt
├── .env.example
├── .gitignore             # include .env and cache/
└── README.md
```

### 2.4 Git
Create a GitHub repo, add everyone, **commit `.env.example` but never `.env`**.

---

## 3. Hours 0–2: Checkpoint 1

- [ ] Submit `README.md` (already written)
- [ ] Add `.env.example`
- [ ] Fill in team names
- [ ] Push repo

---

## 4. Hours 2–8: Build the pieces separately

### 4.1 Common data format (agree on this NOW, all files use it)

Every discovered account looks like this:

```python
candidate = {
    "platform": "github",                  # github / linkedin / x / youtube / instagram / web
    "username": "tech_guru99",
    "display_name": "Johnathan Doe",
    "profile_url": "https://github.com/tech_guru99",
    "bio": "ML engineer. Building NLP tools.",
    "photo_url": "https://avatars.githubusercontent.com/u/123",
    "links": ["https://johndoe.dev"],      # URLs found on the profile
    "location": "Hyderabad",
    "extra": {"repos": [...], "orgs": [...]},   # anything else useful
    "retrieved_at": "2026-01-15T10:32:00Z"
}
```

### 4.2 `bio_matcher.py` (Person B, ~1 hr)

```python
from sentence_transformers import SentenceTransformer, util

_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def bio_similarity(text_a: str, text_b: str) -> float:
    """Returns 0.0–1.0. Higher = more similar meaning."""
    if not text_a.strip() or not text_b.strip():
        return 0.0
    emb = _model.encode([text_a, text_b], convert_to_tensor=True)
    score = util.cos_sim(emb[0], emb[1]).item()
    return max(0.0, min(1.0, score))     # clamp to 0–1

if __name__ == "__main__":
    print(bio_similarity("ML engineer building NLP tools",
                         "I develop natural language processing software"))
    print(bio_similarity("ML engineer building NLP tools",
                         "Professional chef and food blogger"))
```
**Test:** first score should be high (~0.6+), second low (~0.1). If yes, done.

Also add name matching here:

```python
from rapidfuzz import fuzz

def name_similarity(a: str, b: str) -> float:
    return fuzz.token_sort_ratio(a.lower(), b.lower()) / 100
```

### 4.3 `mock_data.json` (Person A, do this FIRST, ~1 hr)

Create **two fake people**. For each one include:
* the "target" (name, context bio, path to a face photo)
* 5–8 candidate accounts: some clearly correct, some clearly wrong (same name, different person), one ambiguous.

This gives you a controlled test set and shows judges the false-match handling.

```json
{
  "targets": [
    {
      "name": "Aarav Mehta",
      "context": "ML engineer in Hyderabad, works on NLP",
      "image": "test_images/aarav.jpg",
      "candidates": [
        {"platform": "github", "username": "aarav-ml", "display_name": "Aarav Mehta",
         "bio": "NLP engineer. Open-source contributor.", "photo_url": "test_images/aarav_gh.jpg",
         "links": ["https://aaravmehta.dev"], "location": "Hyderabad"},
        {"platform": "github", "username": "aarav123", "display_name": "Aarav Mehta",
         "bio": "Chef and food photographer", "photo_url": "test_images/other1.jpg",
         "links": [], "location": "Delhi"}
      ]
    }
  ]
}
```
Use **your own consented photos or AI-generated synthetic faces** for the images.

### 4.4 `osint_fetcher.py` (Person A, ~3 hrs)

Start with GitHub only:

```python
import os, json, time, requests
from dotenv import load_dotenv
load_dotenv()

GH_HEADERS = {"Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"}

def search_github_users(name: str, max_results=5):
    r = requests.get("https://api.github.com/search/users",
                     params={"q": f"{name} in:name", "per_page": max_results},
                     headers=GH_HEADERS, timeout=10)
    r.raise_for_status()
    return r.json().get("items", [])

def get_github_profile(login: str) -> dict:
    u = requests.get(f"https://api.github.com/users/{login}",
                     headers=GH_HEADERS, timeout=10).json()
    repos = requests.get(f"https://api.github.com/users/{login}/repos",
                         params={"sort": "updated", "per_page": 5},
                         headers=GH_HEADERS, timeout=10).json()
    return {
        "platform": "github",
        "username": login,
        "display_name": u.get("name") or login,
        "profile_url": u.get("html_url"),
        "bio": u.get("bio") or "",
        "photo_url": u.get("avatar_url"),
        "links": [x for x in [u.get("blog")] if x],
        "location": u.get("location") or "",
        "extra": {"repos": [{"name": r["name"], "desc": r["description"],
                             "created": r["created_at"]} for r in repos
                            if isinstance(r, dict)]},
        "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
```

Then web search (LinkedIn/X/YouTube/etc.), using search queries such as:
```
"Aarav Mehta" site:linkedin.com/in Hyderabad
"Aarav Mehta" site:x.com
"Aarav Mehta" speaker conference
"Aarav Mehta" patent
```
Convert each result's title/snippet/URL into the candidate format (bio = snippet). **Save every response to `cache/` as JSON** so you never waste API calls.

Master function with fallback:

```python
def discover(name, context, use_mock=False):
    if use_mock:
        return load_mock(name)
    try:
        return live_discovery(name, context)
    except Exception as e:
        print("Live failed, falling back:", e)
        return load_mock(name)
```

**Reality check:** LinkedIn, Instagram, and X do not allow direct scraping. Use only what search results give you (title, snippet, URL, sometimes thumbnail). That is acceptable and matches the "public-only" rule. Say so in the demo.

### 4.5 `face_matcher.py` (Person C, ~2–3 hrs)

**Option A: InsightFace**
```python
import numpy as np, cv2, requests
from insightface.app import FaceAnalysis

_app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
_app.prepare(ctx_id=0, det_size=(640, 640))

def _load(path_or_url):
    if path_or_url.startswith("http"):
        data = requests.get(path_or_url, timeout=10).content
        return cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    return cv2.imread(path_or_url)

def get_embedding(path_or_url):
    img = _load(path_or_url)
    if img is None: return None
    faces = _app.get(img)
    if len(faces) != 1:            # 0 or many faces -> can't trust
        return None
    return faces[0].normed_embedding

def face_similarity(emb_a, emb_b) -> float:
    if emb_a is None or emb_b is None: return None   # None = "no evidence"
    cos = float(np.dot(emb_a, emb_b))                 # already normalized
    # Rescale so ~0.2 (different people) -> 0 and ~0.7 (same person) -> 1
    return max(0.0, min(1.0, (cos - 0.2) / 0.5))
```
Note: for InsightFace, same-person cosine is typically **~0.4–0.8+**, different people **~0.0–0.3**. Test with your own photos and tune a rescale, e.g. `score = clip((cos - 0.2) / 0.5, 0, 1)`.

**Option B: DeepFace fallback**
```python
from deepface import DeepFace
def face_similarity(path_a, path_b):
    r = DeepFace.verify(path_a, path_b, model_name="ArcFace", enforce_detection=False)
    return max(0.0, 1 - r["distance"] / r["threshold"] / 2)
```

**Important:** return `None` (not 0) when a photo has no usable face. "No evidence" is different from "different person," and the resolver uses that difference.

### 4.6 `resolver.py` (Person C, ~2 hrs), the brain

```python
WEIGHTS = {"face": 0.40, "bio": 0.35, "graph": 0.25}

def graph_score(candidate, all_candidates):
    """1.0 if two-way links, 0.5 if one-way, 0 if none."""
    score = 0.0
    for other in all_candidates:
        if other is candidate: continue
        a_to_b = any(other["profile_url"] in l or other["username"] in l
                     for l in candidate["links"])
        b_to_a = any(candidate["profile_url"] in l or candidate["username"] in l
                     for l in other["links"])
        if a_to_b and b_to_a: score = max(score, 1.0)
        elif a_to_b or b_to_a: score = max(score, 0.5)
    return score

def combine(s_face, s_bio, s_graph):
    signals = {"face": s_face, "bio": s_bio, "graph": s_graph}
    available = {k: v for k, v in signals.items() if v is not None}
    total_w = sum(WEIGHTS[k] for k in available)
    conf = sum(WEIGHTS[k] * v for k, v in available.items()) / total_w
    # Safeguard: missing evidence -> can never be auto-verified
    if len(available) < 3:
        conf = min(conf, 0.74)
    # Safeguard: needs at least 2 signals above 0.5 to be verified
    strong = sum(1 for v in available.values() if v >= 0.5)
    if strong < 2:
        conf = min(conf, 0.74)
    return round(conf, 3)

def decide(conf):
    if conf >= 0.75: return "verified"
    if conf >= 0.50: return "needs_review"
    return "rejected"
```

`resolve(target, candidates)` loops over candidates, computes the three scores, calls `combine` + `decide`, and returns a list of dicts including each signal's score and a short human-readable reason (e.g., *"Face 0.81, bio 0.66, links 1.0 → verified"*). **The reason string is what makes the evidence panel impressive.**

### 4.7 `extractor.py` (Person B, ~2 hrs)

Turn text into structured entities. Start rule-based (fast, no cost):
* **Years:** regex `\b(19|20)\d{2}\b`
* **Events:** search snippets containing words like `speaker`, `hackathon`, `conference`, `workshop`, `webinar`, `keynote`
* **Orgs/roles:** patterns like `"X at Company"`, `"Role @ Company"`
* **Projects:** GitHub repos with `created_at` dates
* **Patents/publications:** search results from patent/scholar-type URLs

Output list of:
```python
{"type": "event", "title": "PyCon India talk", "date": "2024",
 "source_url": "...", "snippet": "...", "confidence": 0.8}
```

**Optional boost (only if time remains):** send the snippet to the Claude API with a prompt like "Extract organizations, roles, events, and dates as JSON only." This is much better than regex, but do it last.

---

## 5. Hours 8–14: Build the app

### 5.1 `graph_builder.py` (Person D)
* Center node: the **Target Person**.
* Verified accounts: solid green nodes connected to the center.
* Needs-review accounts: dashed/orange nodes with warning label.
* Rejected: hidden by default (checkbox "show rejected").
* Entities (orgs, events, projects): small nodes connected to the account that produced them.
* Timeline: sort extracted entities by year, show as a simple table or `st.line_chart`/timeline list.

### 5.2 `app.py` (Person D)

Screen layout:
```
[Sidebar] ☐ I confirm this image is consented/authorized (required)
          Upload photo | Name | Location/context | ☐ Use mock data
          [Run Analysis]

[Tab 1: Identity Graph]  streamlit-agraph
[Tab 2: Candidates]      table: platform, username, face, bio, graph, confidence, decision
[Tab 3: Timeline]        chronological events
[Tab 4: Evidence]        click/select a finding → source URL, snippet, timestamp, reason
[Tab 5: Audit log]       download JSON
```

Skeleton:

```python
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

st.set_page_config(page_title="FootprintAI", layout="wide")
st.title("FootprintAI - Digital Identity Intelligence")

with st.sidebar:
    consent = st.checkbox("I confirm this image is consented / authorized for this analysis")
    img = st.file_uploader("Face image", type=["jpg", "jpeg", "png"])
    name = st.text_input("Name")
    context = st.text_input("Context (city, field, org)")
    use_mock = st.checkbox("Use mock data", value=True)
    run = st.button("Run analysis", disabled=not consent)

if run:
    # 1. save uploaded image to temp file
    # 2. candidates = discover(name, context, use_mock)
    # 3. results = resolve(target, candidates)
    # 4. entities = extract(results)
    # 5. store in st.session_state and render tabs
    ...
```
Use `st.session_state` to keep results so the UI doesn't recompute on every click.

**Milestone at hour 14:** enter a name (mock mode) → see graph, scores, and decisions. If you have this, you are on track.

---

## 6. Hours 14–20: Go live and harden

- [ ] Turn on live GitHub + search; keep mock fallback (`try/except` around every network call, with timeouts)
- [ ] Cache all API responses in `cache/`
- [ ] Add **common-name penalty**: if search returns >N accounts with similar names, subtract ~0.05–0.10 from bio/name signals
- [ ] Add **conflict detection**: two "verified" accounts on the same platform → mark both `needs_review`
- [ ] Add **error messages**: no face detected, multiple faces, API down
- [ ] Write **5 test cases** (see §8) and run them
- [ ] Add audit-log download (`st.download_button` with JSON)
- [ ] Take screenshots for the README

---

## 7. Hours 20–24: Demo prep

### 3-minute demo script
| Time | What to show |
|---|---|
| 0:00–0:30 | Problem: fragmented identity, common names, no evidence trail |
| 0:30–1:15 | Tick consent box → upload photo → enter name → run |
| 1:15–2:00 | Graph: verified nodes vs. dashed "unverified" node; point out a rejected same-name impostor |
| 2:00–2:30 | Click a node → evidence panel: source URL, snippet, timestamp, per-signal scores |
| 2:30–2:50 | Timeline + audit log download |
| 2:50–3:00 | Privacy design + limitations (be honest) |

### Prep checklist
- [ ] Rehearse 3 times with a timer
- [ ] Have mock mode ready as backup and **know how to switch in 2 seconds**
- [ ] Pre-run the demo query once so cache is warm
- [ ] Laptop charged, wifi + mobile hotspot backup
- [ ] Pre-loaded browser tab with the app running
- [ ] Prepare answers: *"How do you avoid false matches?"* → three-tier policy + no single-signal merge. *"Privacy?"* → consent gate, public only, no persistence, human review.

---

## 8. Test cases (proves "robustness" marks)

| # | Scenario | Expected result |
|---|---|---|
| 1 | Correct GitHub account, matching face + bio | Verified |
| 2 | Same name, different person (chef vs. engineer) | Rejected |
| 3 | Right person, profile has no photo | Needs review (capped at 0.74) |
| 4 | Two similar accounts on one platform | Both flagged, conflict shown |
| 5 | Photo with no face / multiple faces | Clear error, no crash |
| 6 | API failure | Falls back to mock data, banner shown |

---

## 9. Checkpoint targets

| Checkpoint | Marks | What must exist |
|---|---|---|
| CP1 | 15 | README + `.env.example` |
| CP2 | 25 | Bio matcher, GitHub discovery, resolver, basic UI running with mock data |
| CP3 | 60 | Face matching, multi-platform, graph + timeline, evidence panel, tests, polished demo |

---

## 10. Common beginner problems and fixes

| Problem | Fix |
|---|---|
| `insightface` won't install | Use DeepFace (Option B) |
| Model download is slow | Download `all-MiniLM-L6-v2` and buffalo_l on good wifi **before** the event |
| GitHub API rate limit | Use the token; cache responses |
| SerpAPI runs out | Use `duckduckgo-search`, or cache and rely on mock data |
| Face scores look random | Test on your own photos first; use frontal, clear photos; return `None` when no face |
| Streamlit reruns and loses data | Store results in `st.session_state` |
| Too much to build | **Cut in this order:** Instagram/YouTube specifics → patents → LLM extraction → fancy timeline. **Never cut:** mock fallback, evidence panel, three-tier decisions, consent gate |

---

## 11. Priority list (if time runs short)

**Must have:** consent gate, GitHub discovery, bio matching, resolver with 3 tiers, graph, evidence panel, mock fallback.
**Should have:** face matching, web search for other platforms, timeline, audit download.
**Nice to have:** LLM extraction, common-name penalty, conflict detection UI, exportable report.

Good luck. Get the mock version working end-to-end first, then improve it.
