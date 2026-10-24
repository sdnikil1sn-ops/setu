# Master PRD: Integrated Institution Complaint Monitoring Dashboard

**SIH Problem Statement 26264 · AICTE (Regulation Bureau) · Software / Smart Automation**

*Version 1.0 · Hackathon MVP scope · Authored from the perspective of a senior developer reviewed against an SIH evaluator's lens*

---

## 1. Document Control and Assumptions

| Item | Value |
| --- | --- |
| Product name (working) | **InstitutionWatch** (single-window institution case intelligence for AICTE) |
| Scope | Hackathon MVP: 7 levers + 2 add-ons |
| Data | Synthetic, with a public-style institution master; no real complaint data |
| Deployment target | Runs fully **locally/offline** for the demo; containerized for gov-cloud hosting later |

**Assumptions to confirm**

- The two add-ons are **A: Heads-Up Banner** and **C: Match-Quality Panel** (chosen because they strengthen the core loop; B, "not related" suppression, is folded into Lever 3).
- AICTE Permanent ID exists for most institutions but may be missing or mistyped on complaints.
- Source systems (RB, PGRC) are **simulated** through two adapters with different schemas. Real integration is a roadmap item.
- All thresholds and weights below are **initial defaults to be tuned on synthetic ground truth**, not validated values.

---

## 2. Problem, Root Cause and Users

**Problem.** Complaints about one institution reach AICTE through the Regulation Bureau (RB), the Public Grievance Redressal Cell (PGRC) and other cells. Each tracks cases separately, so overlapping or conflicting actions, delays and ownership confusion go unseen.

**Root cause.** The unit of record is the *case*, not the *institution*. There is no shared institution identity across case registers and no coordination step after overlap is noticed.

**Primary user.** A desk officer (for example in PGRC or RB) about to act on a case, who cannot see what another cell is already doing about the same institution.

| Persona | Need | Key screen |
| --- | --- | --- |
| Desk Officer (RB / PGRC / other cell) | See other cells' open cases on the same institution before acting; coordinate | Case detail with heads-up banner; coordination room |
| Bureau Head | Workload, ageing, overlap in my cell | Bureau dashboard |
| Regional Officer | Cases for my region's institutions | Region-filtered register |
| Senior Management / Competent Authority | Real-time institution and bureau status | Executive dashboard; institution 360 |
| Admin | Manage bureaus, categories, SLA rules, users | Admin config |

**Not users:** students, parents and institutions (no public portal in scope).

---

## 3. Goals, Non-Goals and Success Metrics

### Goals

1. One institution-centric view of every complaint/case across cells.
2. Automatic, **explainable** detection of potentially overlapping cases.
3. A coordination step so overlap leads to a decision, not just an alert.
4. Visible tracking: status, ownership, ageing, SLA, workload.
5. Matching quality that holds for messy names, different wording and Hindi text.

### Non-goals (MVP)

- Public complaint filing portal
- Replacing CPGRAMS or RB/PGRC systems (we are a read-mostly layer on top)
- Auto-merging or auto-closing cases (humans decide)
- Real email/SMS/WhatsApp delivery
- Predictive ML risk scoring; blockchain

### Success metrics

| Metric | Target (MVP, on synthetic benchmark) | How measured |
| --- | --- | --- |
| Overlap detection precision (High tier) | ≥ 90% | Planted ground-truth clusters |
| Overlap detection recall (all tiers) | ≥ 85% | Planted ground-truth clusters |
| Institution resolution accuracy (messy names) | ≥ 95% | Planted name variants |
| Time to answer "what is happening to institution X?" | ≤ 5 seconds / one screen | Demo timing |
| End-to-end demo path runs offline | 100% | Pre-demo checklist |

---

## 4. Scope Overview: 7 Levers + 2 Add-Ons

| ID | Name | Type | Core pain solved | MVP priority |
| --- | --- | --- | --- | --- |
| L1 | Institution identity layer | Core | Same institution invisible across silos | P0 |
| L2 | Explainable overlap detection | Core | Officer unaware another cell is acting | P0 |
| L3 | Coordination room | Core | Detection without a decision still duplicates work | P0 |
| L4 | Visible tracking layer | Core | No single view of status, ageing, workload | P0 |
| L5 | Semantic text similarity | Quality multiplier | Same issue, different wording | P1 (gated on L2) |
| L6 | Trust-group overlap | Quality multiplier | Same trust, different campus | P1 |
| L7 | Multilingual understanding | Quality multiplier / enabler | Hindi complaint never matches English one | P2 |
| A | Heads-up banner | Add-on | Prevents conflicting action at the moment of action | P1 |
| C | Match-quality panel | Add-on | Credibility without real data | P1 |

**Core loop:** Identify → Detect → Explain → Coordinate → Track.

**Build order and cut line:** L1 + L4 → L2 → L3 → **checkpoint (full loop works)** → A → L6 → L5 → C → L7. If time slips, cut in this order: **L7, then L5, then L6**. Never cut L1 to L4.

---

## 5. Functional Requirements

IDs use FR-\<lever>-\<n>. Each lever lists acceptance criteria (AC) that double as demo and test checks.

### L1: Institution Identity Layer (P0)

| ID | Requirement |
| --- | --- |
| FR-1-1 | Maintain a canonical **Institution** record: ID, AICTE Permanent ID (nullable), name, normalized name, address, state/region, optional parent group. |
| FR-1-2 | Maintain **aliases** per institution (abbreviations, former names, spelling variants). |
| FR-1-3 | Resolve every incoming case to an institution: (1) exact Permanent ID; (2) normalized-name + region exact; (3) fuzzy name/address match above a threshold; (4) otherwise queue as **"Unresolved, needs officer confirmation"**. |
| FR-1-4 | Store the resolution **method and confidence** on the case so it can be explained and audited. |
| FR-1-5 | **Institution 360 profile:** details, aliases, group, consolidated chronological case history across all cells, current open cases per cell. |

**AC:** A case with a misspelled name and no ID resolves to the right institution; an ambiguous one lands in the unresolved queue rather than being guessed.

### L2: Explainable Overlap Detection (P0)

| ID | Requirement |
| --- | --- |
| FR-2-1 | On case ingest or update, compute overlap candidates against other **open** cases of the same institution (scope per L6). |
| FR-2-2 | Raise an alert **"Potential Overlapping Cases – Coordination Required"** when candidates exist in **two or more distinct Bureaus/Cells**. |
| FR-2-3 | Every alert carries a **score, tier (High/Medium/Info) and a reasons list** (for example: same institution ID; same category; opened 12 days apart; both open). |
| FR-2-4 | Distinguish **cross-cell overlap** from **same-cell duplicate**. |
| FR-2-5 | Overlap is computed **at ingest/update, not on page load**, and stored as suggested links. |
| FR-2-6 | Detection logic and weights are **configuration**, not hardcoded. |

**AC:** Seeded PGRC and RB cases for one institution produce a High-tier alert with a readable reason list; unrelated cases for different institutions produce none.

### L3: Coordination Room (P0)

| ID | Requirement |
| --- | --- |
| FR-3-1 | From an overlap alert, an authorized officer can **Link**, **Mark "Not related"** or leave **Pending**. |
| FR-3-2 | A dismissed pair **does not re-alert** unless a case materially changes (status, category, transfer). |
| FR-3-3 | Officers can **propose a lead Bureau/Cell** and add timestamped notes; the decision, author and time are recorded. |
| FR-3-4 | Linked cases show each other's status and next action. |
| FR-3-5 | Dismissals are counted toward a **false-positive rate** visible to admins (feeds Add-on C). |

**AC:** An officer links two cases, proposes RB as lead, adds a note; the history shows who decided what and when.

### L4: Visible Tracking Layer (P0)

| ID | Requirement |
| --- | --- |
| FR-4-1 | **Unified case register** with fields: Case ID, receipt date, category, status, current Bureau/Cell, assigned officer, last action, next action, last-action date, expected disposal date. |
| FR-4-2 | **Search/filters:** institution name, Permanent ID, case ID, Bureau/Cell, region, category, status, date range. |
| FR-4-3 | **Status model:** Received, Under Process, Pending, Transferred, Escalated, Disposed. |
| FR-4-4 | **Dashboard KPIs:** total, pending, under process, disposed, transferred, beyond-timeline; institution-wise status; Bureau/Cell-wise workload. |
| FR-4-5 | **Workflow history** per case: chronological actions with officer, Bureau/Cell, timestamp, remarks, attachments, transfer/escalation trail. |
| FR-4-6 | **SLA:** configurable days per category; **amber at 80%** of the limit, **red when breached**; ageing buckets (0–7, 8–15, 16–30, 30+ days). |
| FR-4-7 | **In-app alerts:** overlap, pending reminder, escalation, SLA. |
| FR-4-8 | CSV/PDF export of the current filtered view (a by-product of the filters, not a report builder). |

**AC:** Filtering by region + Bureau + status returns correct counts; a case past its limit turns red and appears in "beyond timeline".

### L5: Semantic Text Similarity (P1, gated on L2)

| ID | Requirement |
| --- | --- |
| FR-5-1 | Compute embeddings of complaint text using a **locally hosted** sentence-embedding model. |
| FR-5-2 | Add semantic similarity as **one more signal** in the L2 score; show it in the reasons ("similar issue: 0.82"). |
| FR-5-3 | Operates only within the **same institution scope**, so it never invents cross-institution links. |
| FR-5-4 | **Gate:** enable only once L2 passes its acceptance criteria on structured fields. |

**AC:** At least one planted overlap is detected **only** because of semantic similarity (different category labels, same underlying issue), and the reason says so.

### L6: Trust-Group Overlap (P1)

| ID | Requirement |
| --- | --- |
| FR-6-1 | Institutions may belong to a **parent group** (trust/society). |
| FR-6-2 | The overlap query takes a **scope parameter**: `campus`, `group`, `region`. Default `campus`. |
| FR-6-3 | Group-scope alerts are labeled distinctly and shown with the affected campuses. |
| FR-6-4 | Demo seed: one trust with three campuses and cases across them. |

**AC:** Changing scope from `campus` to `group` surfaces cases on sibling campuses without code changes.

### L7: Multilingual Understanding (P2)

| ID | Requirement |
| --- | --- |
| FR-7-1 | Use a **multilingual embedding model** so Hindi and English complaint texts are comparable (a model choice, not a translation pipeline). |
| FR-7-2 | Store the complaint's language; render **Devanagari** correctly with a self-hosted font. |
| FR-7-3 | Demo with 2 to 3 Hindi complaints that match English ones. |

**AC:** A Hindi complaint about the same issue as an English one at the same institution appears in the overlap reasons.

> L7 is an enabler for L5, not a standalone feature; it gets no screen of its own.

---

## 6. Add-Ons

### Add-on A: Heads-Up Banner (P1)

| ID | Requirement |
| --- | --- |
| FR-A-1 | On every case detail page, show a banner when the institution has other open cases in other cells: *"This institution has N other open cases in PGRC and RB."* with link to the cluster. |
| FR-A-2 | Banner reads from stored L2 results (no new matching logic) and respects RBAC and restricted-case rules. |

**Why:** shifts the product from *detecting* overlap to *preventing* it at the moment of action; near-zero build risk.

### Add-on C: Match-Quality Panel (P1)

| ID | Requirement |
| --- | --- |
| FR-C-1 | An evaluation script runs the overlap engine against **planted ground truth** and reports precision, recall and institution-resolution accuracy. |
| FR-C-2 | A small admin screen (or slide-ready output) shows the metrics, the false-positive rate from L3 dismissals, and examples of misses. |

**Why:** answers the hardest judge question ("How do you know it works without real data?") with measured numbers and honest limits.

---

## 7. Data Model

| Entity | Key fields |
| --- | --- |
| **Institution** | id, permanent\_id (nullable), name, normalized\_name, address, region, state, group\_id (nullable) |
| **InstitutionAlias** | institution\_id, alias |
| **InstitutionGroup** | id, name (trust/society) |
| **Bureau** | id, name, type (data, not code); supports adding new cells without code changes |
| **User** | id, name, role, bureau\_id, region\_id |
| **Case** | id, case\_ref, source\_system, source\_ref, institution\_id, institution\_name\_raw, resolution\_method, resolution\_confidence, category, text, language, status, current\_bureau\_id, assigned\_user\_id, received\_date, last\_action, last\_action\_date, next\_action, expected\_disposal\_date, is\_restricted |
| **CaseAction** | id, case\_id, action\_type, from\_bureau, to\_bureau, actor, timestamp, remarks, attachment\_ref |
| **CaseLink** | id, case\_a, case\_b, state (suggested / linked / dismissed), score, tier, reasons (JSON), scope, decided\_by, decided\_at, note |
| **CoordinationNote** | id, link\_id, author, timestamp, text, proposed\_lead\_bureau |
| **Alert** | id, type (overlap / pending / escalation / sla), case\_id or link\_id, created\_at, acknowledged\_by |
| **SLARule** | category, limit\_days, amber\_pct |
| **AuditLog** | id, actor, action, entity, timestamp, prev\_hash, hash (hash-chained, optional stretch) |

**Design rules**

- Bureaus, categories, SLA rules and scopes are **data**, so a judge can ask for a new cell or rule and you change config, not code.
- `group_id` exists from day one so L6 is not a migration.
- Source-specific fields stay in the adapter; the canonical Case model is source-agnostic (also keeps the core **regulator-agnostic** should regulators consolidate in future).

---

## 8. Overlap Engine Specification

**Pipeline (runs at ingest and on material update)**

1. **Resolve institution** (L1): Permanent ID → normalized name+region → fuzzy → unresolved queue.
2. **Select candidates:** other open cases within scope (campus by default; group/region per L6).
3. **Score each pair** using signals:

| Signal | Meaning | Initial weight |
| --- | --- | --- |
| Same institution (deterministic) | Gate: required within campus scope | gate |
| Resolution confidence | Reliability of the institution match | 0.15 |
| Same/related category | Category match or mapping | 0.25 |
| Time proximity / both open | Concurrent or near in time | 0.20 |
| Different Bureau/Cell | Required for cross-cell alert | gate |
| Semantic similarity (L5/L7) | Embedding cosine, same institution only | 0.30 |
| Group scope (L6) | Sibling campus, lowers confidence slightly | modifier |

4. **Tier:** High ≥ 0.75, Medium 0.50 to 0.75, Info 0.30 to 0.50 (initial values; tune on the planted set).
5. **Emit reasons** for every contributing signal, in plain language.
6. **Persist** as `CaseLink(state=suggested)`; skip pairs already dismissed unless a case changed.

**Principles:** explainable over clever; deterministic first, semantic second; **never auto-act**, only suggest; every flag shows *why*.

---

## 9. Architecture and Interfaces

| Layer | Choice |
| --- | --- |
| Frontend | React/Next.js, Tailwind, Recharts/ECharts; **locally bundled** fonts and icons (including Noto Sans Devanagari) |
| Backend | FastAPI (Python) |
| Database | PostgreSQL with `pg_trgm` for fuzzy matching |
| Matching | RapidFuzz; sentence-transformers multilingual model **loaded from a local path** |
| Jobs | Scheduler for SLA recomputation and overlap recomputation |
| Auth | Local JWT with RBAC (seeded demo users) |
| Packaging | Docker Compose; single start and reset script |

**Key endpoints (illustrative)**

- `GET /institutions/{id}` (360 profile), `GET /institutions/resolve?name=...`
- `GET /cases` with the 8 filters; `GET /cases/{id}` including banner data; `GET /cases/{id}/history`
- `POST /cases/ingest/{source}` (adapter entry point)
- `GET /overlaps?scope=campus|group|region`; `POST /links/{id}/decision` (link / dismiss / propose lead)
- `GET /dashboard/kpis`; `GET /dashboard/workload`; `GET /alerts`
- `GET /admin/match-quality`; `POST /admin/reset-demo`

**Source adapters:** two simulated adapters (RB-style and PGRC-style schemas) normalize into the canonical Case model. This is the declared mock boundary.

---

## 10. Security, Privacy and Access

- **RBAC** by Bureau/Cell and region; Admin and Management roles for cross-cell views.
- **Field-level masking:** complainant identity visible only to the owning cell; other cells see case metadata.
- **Restricted cases** (confidential or sub-judice): other cells see only a minimal indicator ("a restricted case exists, contact Cell X").
- All views of restricted data and all decisions are written to the audit log (hash-chained as a stretch goal).
- No real personal data in the prototype; encryption in transit and at rest described as the production target.
- Aligned with data-protection obligations (DPDP Act 2023); legal review is a production step, not an MVP claim.

---

## 11. Non-Functional Requirements

| Area | Requirement |
| --- | --- |
| Offline | Entire demo path works with **no internet** (no CDN, no model download, no external API at runtime) |
| Performance | Register and dashboard respond in under 2 seconds at about 10,000 synthetic cases; overlap computed at ingest |
| Reliability | One-command start and reset; health-check page |
| Portability | API base URL via environment/relative path; servers bind to `0.0.0.0`; verified from a **second device** |
| Usability | The overlap alert answers who, what, why, and what next in about 5 seconds |
| Time | Seed dates relative to "now" so SLA and ageing look correct on demo day |

---

## 12. Synthetic Data and Evaluation Plan

- **Institutions:** about 500 to 2,000, built from public-style names/regions with injected variants (typos, abbreviations, Hindi transliteration), plus several trusts with multiple campuses.
- **Cases:** about 5,000 to 10,000 across categories (fees/refund, faculty, infrastructure, approval status, admission, others), in two source schemas.
- **Planted ground truth:** known overlap clusters, including (a) exact-ID overlaps, (b) messy-name overlaps, (c) different-wording overlaps, (d) Hindi/English pairs, (e) cross-campus group overlaps, and (f) **decoys** that look similar but are unrelated.
- **Generation happens before the demo** and is saved as seed files; the running app makes no LLM calls.
- **Metrics reported (Add-on C):** precision/recall per tier, institution-resolution accuracy, false-positive rate, and a list of known misses.

**Honest limitation to state:** results are on synthetic data; real-world accuracy requires calibration on actual cases during a pilot.

---

## 13. Demo Script (3 Minutes)

1. **Institution 360** for College X: two open cases in two cells.
2. **New complaint** arrives with a misspelled college name → resolves to College X → overlap alert with reasons (L1, L2).
3. **Heads-up banner** on the case page shows other cells' open cases (Add-on A).
4. **Coordination room:** link the cases, propose RB as lead, add a note (L3).
5. **Hindi complaint** on the same issue is matched through the semantic signal (L5, L7).
6. **Group scope:** switch to `group` and see sibling-campus cases (L6).
7. **Dashboard:** SLA alert and Bureau workload (L4); close on the **match-quality panel** (Add-on C).

---

## 14. Risks and Mitigations

| Risk | Likelihood / impact | Mitigation |
| --- | --- | --- |
| Embedding model fails to load offline | Medium / High | Pre-download; load from local path; offline flag; test in airplane mode |
| Too many levers, half-built result | High / High | Strict build order and cut line; checkpoint after L3 |
| False positives overwhelm officers | Medium / Medium | Tiers, "not related" suppression, grouped alerts, FP-rate visibility |
| No real data; accuracy challenged | High / Medium | Planted ground truth, published metrics, honest limits |
| Hardcoded localhost breaks on other devices | Medium / High | Env/relative API URL; second-device test |
| Hosted app cold start or outage | Medium / Medium | Demo locally; hosted link is optional |
| Confidentiality questions | Medium / Medium | RBAC, masking, restricted-case indicator |
| Regulator restructuring makes AICTE-specific design obsolete | Low / Medium | Bureaus and regulators as data; canonical, source-agnostic model |

---

## 15. Evaluator Scorecard (Self-Assessment)

| Criterion | What we show | Gap to be honest about |
| --- | --- | --- |
| Alignment with PS | All 8 feature areas mapped to levers L1 to L7 | Real source integration is simulated |
| Innovation | Explainable, multi-signal overlap detection and a coordination room | Semantic/multilingual quality depends on synthetic benchmark |
| Feasibility | Complete core loop on real logic; mocks only at the edges | Production connectors need MoU and secure access |
| Impact | Fewer duplicate actions, faster visibility, management oversight | No baseline volume data yet; do not quote invented statistics |
| Scalability | Source-agnostic model; Bureaus/regulators as data | Needs load testing at production volume |
| Security and governance | RBAC, masking, restricted cases, audit trail | Formal compliance review pending |
| UX | Alert answers who/what/why/next in about 5 seconds | Needs usability testing with real officers |

---

## 16. Roadmap Beyond MVP

1. Real connectors to RB/PGRC/CPGRAMS-style sources and an institution master sync.
2. Category-specific SLA calendars with working-day and pause/resume logic.
3. Learning from officer feedback to tune thresholds.
4. Multi-regulator support if regulators consolidate.
5. Role-based report builder; notification channels with real delivery.

---

## 17. Open Questions

1. Exact fields and formats of the real AICTE Permanent ID and source systems' identifiers.
2. Which complaint categories and SLA limits AICTE actually prescribes per category.
3. Whether same-cell duplicates should be auto-suggested for merge or only flagged.
4. Who owns the final call when cells disagree on the lead (policy, not software).
5. Retention and confidentiality rules for restricted and sub-judice cases.
