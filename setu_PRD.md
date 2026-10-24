# Setu --- Ultimate Master Product Requirements Document

## SIH Problem Statement 26264 \| AICTE \| Prototype Build Specification

**Version:** 2.0\
**Status:** Consolidated specification for prototype creation\
**Date:** 25 October 2026\
**Product type:** Offline-first, institution-centred complaint
intelligence and cross-bureau coordination platform\
**Working name:** InstitutionWatch\
**Primary deliverable:** A demonstrable, locally runnable prototype with
synthetic data and explainable overlap detection

------------------------------------------------------------------------

## 0. How to use this document

This is the single source of truth for the prototype. Product, UI,
backend, database, testing, and demo work should follow it. If a
requirement is unclear, use the explicit defaults in this document and
record any deviation as an architecture decision.

This PRD combines the supplied `prd.md` with the broader product,
security, data-model, testing, and implementation requirements developed
for PS26264. The uploaded PRD's core design is retained: seven levers,
two add-ons, an institution identity layer, explainable overlap
detection, a coordination room, visible tracking, simulated RB/PGRC
adapters, and offline demo execution.

**Important distinction:** The title and problem framing are associated
with SIH PS26264. This document is a proposed product specification, not
an official AICTE policy document. Deadlines, permissions, case states,
matching thresholds, and operational procedures must be confirmed with
the problem owner before production use.

## 1. Product definition

### 1.1 Product vision

**One institution. One connected case history. Multiple responsible
bureaus. Clear accountability from complaint receipt to coordinated
action.**

InstitutionWatch is an internal, institution-centred case intelligence
layer for authorized AICTE personnel. It consolidates complaint/case
records from separate bureaus or cells, identifies potentially
overlapping cases, explains why they may be related, gives staff a
structured way to coordinate, and makes ownership, status, ageing,
deadlines, and case history visible.

It is not merely a dashboard and is not intended to replace official
complaint-handling systems in the prototype.

### 1.2 Problem statement and root cause

Institution-related complaints may reach the Regulation Bureau (RB),
Public Grievance Redressal Cell (PGRC), and other units through separate
registers or systems. Staff may lack a consolidated view of what other
units are doing about the same institution or issue. This can make
overlapping work, delays, conflicting actions, and unclear ownership
harder to identify.

The underlying product hypothesis is that the unit of record is often
the individual case, while the coordination need is institution- and
issue-centred. The platform therefore needs both: - a canonical
institution identity that connects records across sources; and - a
separate case identity that preserves each complaint's own lifecycle,
owner, evidence, and decision history.

The actual frequency and severity of these problems must be validated
with AICTE stakeholders.

### 1.3 Primary users

  -----------------------------------------------------------------------
  Persona                 Main need               Main screens
  ----------------------- ----------------------- -----------------------
  Desk officer in RB,     See relevant cases in   Case detail, heads-up
  PGRC, or another cell   other cells before      banner, coordination
                          acting; record case     room
                          work                    

  Bureau/Cell coordinator Review overlaps,        Overlap queue,
                          coordinate actions,     coordination room,
                          resolve ownership       bureau dashboard
                          conflicts               

  Bureau head             Understand workload,    Bureau dashboard,
                          ageing, and unresolved  filtered register
                          overlaps within a       
                          bureau                  

  Regional officer        Review cases for        Region-filtered
                          institutions in an      register, institution
                          authorized region       360

  Senior management /     Understand cross-bureau Executive dashboard,
  competent authority     status and bottlenecks  institution 360,
                                                  reports

  System administrator    Configure users, roles, Admin configuration,
                          bureaus, categories,    match-quality panel
                          matching rules, and SLA 
                          settings                

  Auditor / read-only     Inspect permitted       Case history, audit
  reviewer                histories and decisions views
  -----------------------------------------------------------------------

**Out of scope as users for the prototype:** students, parents, and
institutions. No public complaint filing portal is required.

### 1.4 Product goals

1.  Provide one institution-centric view of permitted complaint/case
    records across cells.
2.  Detect potential overlapping cases automatically and explain the
    signals.
3.  Turn an overlap alert into an explicit, auditable coordination
    decision.
4.  Show status, current owner, bureau, last action, next action,
    ageing, deadlines, and workload.
5.  Resolve messy institution names safely without guessing when
    identity is ambiguous.
6.  Demonstrate the complete core workflow offline with synthetic data.
7.  Measure matching quality against planted synthetic ground truth
    rather than making unsupported claims.

### 1.5 Non-goals for the MVP

-   Public complaint submission or complainant self-service.
-   Replacing CPGRAMS, RB, PGRC, or other official source systems.
-   Real source-system integration; source adapters are simulated for
    the prototype.
-   Automatic merging, closure, or adjudication of complaints.
-   Automatic conclusions about institutional wrongdoing.
-   Real email, SMS, or WhatsApp delivery.
-   Predictive ML risk scoring or blockchain infrastructure.
-   Mandatory cloud deployment or runtime internet access.
-   Training a custom large language model.

## 2. Product principles and non-negotiable rules

1.  **Institution identity and case identity are different.** Multiple
    cases can belong to one institution without being duplicates.
2.  **Explainable over clever.** Every suggested relationship must show
    its reasons.
3.  **Suggest, never silently act.** Humans confirm, dismiss, defer,
    transfer, and close cases under authorization rules.
4.  **No auto-merge or auto-close.** Related cases keep their
    independent IDs and histories.
5.  **Ambiguity must be visible.** An uncertain institution match goes
    to an unresolved queue rather than being guessed.
6.  **Security applies to every view and API.** UI hiding alone is not
    access control.
7.  **Data provenance matters.** Preserve source system, source
    reference, matching method, and confidence.
8.  **Offline-first demo.** No CDN, external API, runtime model
    download, or internet dependency during the demo.
9.  **Synthetic data only.** No real personal complaint data in the
    prototype.
10. **Configuration over hardcoding.** Bureaus, categories, scopes,
    thresholds, and SLA rules should be stored as data.
11. **Status, priority, and SLA health are independent dimensions.**
12. **A dashboard number must be traceable to persisted records and a
    documented formula.**

## 3. Scope model: seven levers plus two add-ons

  -------------------------------------------------------------------------
  ID                Capability          Priority          Prototype
                                                          decision
  ----------------- ------------------- ----------------- -----------------
  L1                Institution         P0                Required
                    identity layer and                    
                    Institution 360                       

  L2                Explainable overlap P0                Required
                    detection                             

  L3                Coordination room   P0                Required

  L4                Visible tracking,   P0                Required
                    SLA, alerts, and                      
                    dashboard                             

  L5                Semantic text       P1                Add only after
                    similarity with                       L1--L4 and
                    local embeddings                      structured L2
                                                          pass

  L6                Trust/group-level   P1                Design schema
                    overlap across                        from day one;
                    campuses                              implement after
                                                          core loop

  L7                Multilingual        P2                Stretch; only if
                    understanding,                        offline model and
                    including                             time allow
                    Hindi-English                         
                    matching                              

  Add-on A          Heads-up banner on  P1                Implement after
                    case detail                           core loop; reads
                                                          stored overlap
                                                          results

  Add-on C          Match-quality panel P1                Implement after
                    and evaluation                        overlap engine
                    report                                and ground-truth
                                                          tests
  -------------------------------------------------------------------------

**Core loop:** Identify → Detect → Explain → Coordinate → Track.

**Build order:** Foundation and L1/L4 → L2 → L3 → validate complete core
loop → heads-up banner → L6 → L5 → match-quality panel → L7.

**Cut line if time is short:** Cut L7 first, then L5, then L6. Do not
cut L1, L2's explainability, L3's human decision step, L4's tracking, or
basic security.

## 4. Functional requirements

Requirement priorities: - **P0:** Required for a credible prototype. -
**P1:** Important differentiator after the core loop works. - **P2:**
Stretch capability.

### 4.1 L1 --- Institution identity layer (P0)

**FR-1.1 Canonical institution record** Maintain an institution record
with: - internal immutable ID; - AICTE Permanent ID, nullable until
verified; - canonical name and normalized name; - address, state,
district/region; - optional parent institution group/trust; -
verification status and provenance; - created/updated timestamps.

**FR-1.2 Institution aliases** Store aliases, abbreviations, previous
names, spelling variants, and approved transliterations linked to the
canonical institution. Record source and verification state where
practical.

**FR-1.3 Institution resolution order** Resolve an incoming case in this
order: 1. Exact verified AICTE Permanent ID. 2. Exact normalized name
plus region/state. 3. Alias match plus region/state. 4. Fuzzy
name/address match above a configurable threshold. 5. Otherwise set
institution resolution to `unresolved` and queue it for authorized
officer confirmation.

Do not force a match when more than one candidate is plausible.

**FR-1.4 Resolution provenance** Persist resolution method,
confidence/score, candidate evidence, and whether the result was
manually confirmed. Scores are matching estimates, not probabilities of
misconduct.

**FR-1.5 Institution 360** Show, subject to access control: - canonical
identity, aliases, group, and verification status; - chronological cases
from all permitted source cells; - open cases by bureau/cell; - status,
owner, last action, next action, expected disposal date; - suggested and
confirmed relationships; - coordination records and permitted evidence
references; - data provenance and last-updated time.

**Acceptance criteria** - A misspelled name with a unique, strong match
resolves to the correct synthetic institution. - An ambiguous name is
placed in the unresolved queue. - Exact verified IDs outrank fuzzy name
similarity. - Correcting an institution match preserves the prior
resolution in history. - Two different campuses are not merged merely
because their names are similar.

### 4.2 L2 --- Explainable overlap detection (P0)

**FR-2.1 Trigger** Run overlap candidate generation at case ingest and
on material case updates, not on every page load. Material changes
include institution resolution, category, text, status, bureau transfer,
and scope-relevant group assignment.

**FR-2.2 Candidate selection** Default scope is `campus`: compare with
other open cases linked to the same canonical institution. Same-cell
duplicates may be suggested but must be distinguished from cross-cell
overlap. A cross-cell alert requires cases in at least two distinct
bureaus/cells.

**FR-2.3 Alert label** Use the exact user-facing label: **"Potential
Overlapping Cases --- Coordination Required."**

**FR-2.4 Score, tier, reasons** Every candidate should contain: -
score; - tier (`High`, `Medium`, `Info`); - matching signals and
readable reasons; - source cases and their bureau/status; - scope
(`campus`, `group`, or `region`); - generated timestamp; - review state.

**FR-2.5 Explainable deterministic signals** Initial signals may
include: - same verified institution ID (gate for campus scope); -
institution-resolution confidence; - same or related category; - time
proximity and both cases being open; - different bureau/cell; - semantic
similarity, only when L5/L7 is enabled; - group-scope modifier for
sibling campuses.

**FR-2.6 Configurable weights** Store weights, gates, and tier
thresholds in configuration. Do not bake policy thresholds into UI code.
Validate configuration so weights and thresholds are sensible.

**FR-2.7 Initial scoring defaults** Use the following as initial tunable
defaults, not validated values: - institution-resolution confidence:
0.15; - same/related category: 0.25; - time proximity / both open:
0.20; - semantic similarity: 0.30 when enabled; - same institution and
cross-cell conditions are gates, not additive evidence; - group scope
applies a configurable confidence modifier.

Initial tiers: - High: score ≥ 0.75 - Medium: 0.50 ≤ score \< 0.75 -
Info: 0.30 ≤ score \< 0.50 - Below Info threshold: do not show as an
overlap alert by default, but allow diagnostic evaluation.

The scoring function must normalize enabled signals and document how
missing signals are treated. Do not silently treat a missing semantic
score as zero if semantic matching is disabled.

**FR-2.8 Persist suggestions** Persist suggested links so dashboards and
case pages read stored results. Avoid duplicate candidate records for
the same canonical case pair and scope.

**FR-2.9 Dismissal suppression** A dismissed pair should not re-alert
unless a material change occurs. Store dismissal reason, actor, and
timestamp. A material change may create a new review version or reset
suppression according to configurable policy.

**FR-2.10 No automated action** Overlap results must never automatically
merge, close, transfer, or adjudicate cases.

**Acceptance criteria** - Seeded open cases for one institution in PGRC
and RB generate an explainable cross-cell candidate. - The alert names
both cases and their current cells. - Unrelated cases belonging to
different institutions do not produce a campus-scope overlap. - A case
pair's score and reasons can be reproduced from the stored signals and
configuration. - Repeated page loads do not rerun matching. - A
dismissed pair stays suppressed until a material change occurs.

### 4.3 L3 --- Coordination room (P0)

**FR-3.1 Review actions** An authorized officer may: - `Link` the cases
as related; - mark the suggestion `Not related`; - leave it `Pending`; -
propose a lead bureau/cell; - add a timestamped coordination note.

**FR-3.2 Separate identity** Linking creates a relationship, not a
merge. Both case records, owners, histories, evidence references, and
dispositions remain independent.

**FR-3.3 Lead bureau** A user may propose a lead bureau. The system must
distinguish a proposal from an approved decision if policy requires
approval. For the prototype, a coordinator can confirm the lead
designation and the audit history records it.

**FR-3.4 Shared view** Linked cases display each other's permitted
status, bureau, last action, next action, and coordination notes.
Restricted-case rules override this view.

**FR-3.5 Decision history** Store the decision, author, timestamp, note,
and previous review state. Provide an audit trail for link/unlink and
lead-bureau changes.

**FR-3.6 False-positive feedback** Count dismissed suggestions and
include them in the match-quality panel. Treat dismissal as feedback for
evaluation, not as automatic model training.

**Acceptance criteria** - Officer links two cases, proposes RB as lead,
and adds a note. - Case relationship history shows who decided what and
when. - An officer can mark a false positive and the pair is suppressed
as configured. - Unlinking requires authorization and a reason. - No
case data is lost when links change.

### 4.4 L4 --- Visible tracking layer (P0)

**Unified case register fields** - Case ID and source reference; -
received date; - institution name and Permanent ID when available; -
category and short subject; - status; - current bureau/cell; - assigned
officer; - last action and last-action date; - next action; - expected
disposal date; - SLA health/ageing; - overlap indicator; - restriction
indicator where permitted.

**FR-4.1 Search and filters** Support composable filters for: -
institution name; - Permanent ID; - case ID and external reference; -
bureau/cell; - state/region/district; - category; - status; - assigned
officer where permitted; - date range; - SLA health; - overlap review
state.

**FR-4.2 Status model** Use the prototype statuses: - `Received` -
`Under Process` - `Pending` - `Transferred` - `Escalated` - `Disposed`

Keep status distinct from SLA health (`On Track`, `Amber / Due Soon`,
`Beyond Timeline`, `Paused`) and priority. Allowed transitions must be
defined and enforced server-side. Example: a disposed case may be
reopened only through a permitted, reasoned action if reopening is
enabled.

**FR-4.3 Dashboard KPIs** Show: - total cases; - received cases in
selected period; - pending; - under process; - disposed; -
transferred; - escalated; - beyond-timeline; - unresolved institution
mappings; - suggested cross-cell overlaps; - pending coordination
decisions; - bureau/cell workload; - institution-wise status; - ageing
buckets.

Every KPI must define its formula, date window, scope, and drill-down.
Do not hard-code counts.

**FR-4.4 Workflow history** Per case, show a chronological timeline
containing actor, bureau/cell, timestamp, action type, remarks,
assignment/transfer/escalation trail, and authorized attachment
references.

**FR-4.5 SLA rules** Store configurable days per category. Initial UI
defaults: - amber at 80% of configured limit; - red/beyond timeline when
breached; - ageing buckets: 0--7, 8--15, 16--30, and 30+ days.

The boundary for the final bucket should avoid double-counting: use 31+
days in implementation if the first three buckets are inclusive. Display
the chosen definitions clearly.

These are prototype defaults, not official AICTE timelines. Production
policy must be confirmed.

**FR-4.6 In-app alerts** Support overlap, pending reminder, escalation,
and SLA alerts. Alerts have read/acknowledged state and link to the
relevant case or relationship.

**FR-4.7 Export** Export the current authorized, filtered view to CSV.
PDF export is desirable if time allows. Exports must respect the same
access and field-masking rules as the UI.

**Acceptance criteria** - Combining region + bureau + status produces
correct records and counts. - A case past its configured limit is marked
beyond timeline and appears in the relevant queue. - KPI totals
reconcile with equivalent authorized database queries. - Timeline
ordering is stable and timestamps are server-generated. - Exported rows
match the visible filtered result within the user's permissions.

### 4.5 Add-on A --- Heads-up banner (P1)

On every case detail page, display a banner when other open cases exist
for the same institution in other cells, subject to authorization.

Example: "This institution has 2 other open cases in PGRC and RB."

The banner: - reads persisted overlap/case results; - links to the
permitted case cluster; - shows minimal information for restricted
cases; - does not run a separate matching algorithm; - never reveals
complainant identity or restricted content to unauthorized cells.

### 4.6 L5 --- Semantic text similarity (P1, gated)

Implement only after structured L2 matching meets its acceptance tests.

-   Use a locally hosted sentence-embedding model loaded from a local
    path.
-   No model download or external API call at runtime.
-   Compute embeddings at ingest/update and persist model/version
    metadata.
-   Use semantic similarity as one signal, not the sole decision.
-   Restrict semantic matching to the same institution scope for campus
    mode.
-   Show the score and an understandable reason, e.g. "Complaint wording
    is semantically similar (0.82)."
-   Provide a configuration switch to disable semantic matching.
-   If the model is unavailable, deterministic matching must still work
    and the UI must report the reduced mode honestly.

### 4.7 L6 --- Trust/group overlap (P1)

-   Institutions may belong to a parent group, trust, or society.
-   Group fields must exist in the initial schema even if group matching
    is deferred.
-   Overlap query accepts `scope=campus|group|region`.
-   Default scope is `campus`.
-   Group-scope alerts are visibly labelled and identify the affected
    campuses.
-   Group scope must lower confidence or add a distinct modifier because
    shared ownership does not prove a shared issue.
-   Demo data includes one group with three campuses and cases across
    campuses.

### 4.8 L7 --- Multilingual understanding (P2)

-   Store complaint language when known or detected.
-   If enabled, use a local multilingual embedding model so Hindi and
    English complaint texts can be compared without requiring a
    translation pipeline.
-   Bundle a self-hosted font that correctly renders Devanagari, such as
    Noto Sans Devanagari, subject to license/packaging review.
-   Seed two or three Hindi complaints that correspond to English issue
    descriptions.
-   No screen is dedicated solely to multilingual matching; it appears
    as a reason within the overlap panel.
-   If the local model is not packaged and tested offline, omit this
    feature rather than making a runtime network call.

### 4.9 Intake and source adapters

The prototype does not replace official source systems. It simulates two
distinct source formats: - RB-style adapter; - PGRC-style adapter.

Each adapter normalizes source-specific fields into a canonical case
model. Source-specific quirks stay in the adapter, not in the core case
entity.

Required behavior: - preserve `source_system` and `source_ref`; -
validate incoming data; - make ingestion idempotent; - record rejected
rows and reasons; - resolve institution identity; - compute overlap
candidates after successful persistence; - never expose adapter secrets
or source-specific internal payloads to the browser.

Provide a small seeded demo flow or UI action to simulate a new incoming
case. A real connector is roadmap scope only.

### 4.10 Case assignment, transfer, and resolution

-   Every active case should have a current responsible bureau/cell.
-   Assignment changes create history records.
-   Transfer requires an authorized actor and reason; receiving
    acknowledgement may be simulated if required.
-   Coordination participation does not automatically transfer
    ownership.
-   Closure/disposal requires required resolution fields and an
    authorized action.
-   Reopening, if enabled, requires reason and records the prior
    disposition.
-   Case status transitions must be transactional.
-   No routine hard deletion of complaint history.

### 4.11 Evidence and attachments

For prototype scope: - use synthetic files or safe fixture documents
only; - store files privately or keep metadata-only fixtures if secure
local storage is not ready; - validate size and type server-side; - do
not trust filename extension alone; - associate each evidence reference
with a case, uploader, and timestamp; - enforce authorization on every
download; - preserve evidence history when an attachment is replaced or
withdrawn.

Malware scanning, production object-storage hardening, and retention
policy need production review.

### 4.12 Admin configuration and match-quality panel (Add-on C, P1)

Admin-configurable data: - bureaus/cells; - categories; - institution
groups; - overlap scopes; - matching weights and thresholds; - SLA days
and amber percentage; - user roles and bureau/region scope.

**Match-quality panel requirements** - evaluation script runs against
planted ground truth; - report precision and recall by tier; - report
institution-resolution accuracy; - report false-positive rate based on
dismissed suggestions; - show known misses and representative false
positives; - display benchmark size and date/version; - clearly state
results are from synthetic data.

Do not present synthetic benchmark metrics as production accuracy.

## 5. User experience and required screens

### 5.1 Global navigation

Recommended primary navigation: 1. Executive/Bureau Dashboard 2. Case
Register 3. Institutions 4. Overlap Review 5. Coordination 6. Alerts 7.
Reports 8. Admin (authorized roles only)

Keep the UI focused on a staff workflow, not a public complaint portal.

### 5.2 Screen specifications

**Screen 1 --- Login / demo identity** - Local demo authentication or
seeded demo users. - Clearly show the active role and bureau/region
scope. - Provide safe, documented demo credentials for local use only. -
Never use production-like shared credentials outside the prototype.

**Screen 2 --- Dashboard** - KPI cards and selected-period filter. -
Bureau workload and ageing. - Beyond-timeline queue. - Pending overlap
reviews. - Unresolved institution identity queue. - Every card drills
into a filtered register.

**Screen 3 --- Unified case register** - Search bar, composable filters,
sort, pagination. - Columns listed in L4. - Status and SLA badges use
consistent labels. - Overlap and restriction indicators must not leak
protected details.

**Screen 4 --- Case detail** - Case summary and institution identity
resolution. - Heads-up banner when applicable. - Status, owner, bureau,
next action, deadline. - Timeline and permitted attachments. -
Suggested/confirmed relationships. - Authorized actions: assign,
transfer, add note, change status, propose resolution. - Show why an
institution was matched and whether that match was manually confirmed.

**Screen 5 --- Institution 360** - Institution identity, aliases, group,
and verification. - Summary of cases by bureau and status. -
Chronological case list. - Relationship cluster and coordination
records. - Unresolved identity warnings where relevant.

**Screen 6 --- Overlap review** - Pair/cluster of cases. - Score and
tier. - Reasons list with signal-level detail. - Same-cell vs cross-cell
vs group-scope label. - Review actions: Link, Not related, Pending. -
Audit history of prior decisions.

**Screen 7 --- Coordination room** - Linked cases and current status. -
Proposed/confirmed lead bureau. - Notes with author and timestamp. -
Agreed next actions and due dates. - Clear separation of coordination
status from each case's status.

**Screen 8 --- Alerts** - Overlap, pending, escalation, SLA. -
Acknowledge/read state. - Filters and links to source record. -
Restricted records reveal only authorized details.

**Screen 9 --- Admin configuration** - Manage users/roles, bureaus,
categories, group memberships, SLA rules, matching weights, and
scopes. - Validate configuration changes. - Record admin changes in
audit history.

**Screen 10 --- Match-quality panel** - Precision, recall, institution
resolution accuracy, false-positive rate. - Benchmark version and
size. - Example false positives and known misses. - Clear synthetic-data
disclaimer.

### 5.3 Interaction and accessibility rules

-   The overlap alert should answer: **Who? What? Why? What next?**
-   A staff member should be able to understand an alert in about five
    seconds.
-   Every action with consequences must have a clear label and
    confirmation where appropriate.
-   Show empty, loading, error, permission-denied, and unresolved
    states.
-   Use keyboard-accessible controls and readable contrast.
-   Do not communicate status by color alone.
-   Use local fonts/icons; no runtime CDN dependencies.
-   Layout must work on a typical laptop and be usable from a second
    device on the local network.

## 6. Data model

Use a canonical relational model. Source-specific fields remain in
adapters.

### 6.1 Core entities

  -----------------------------------------------------------------------
  Entity/table                        Important fields
  ----------------------------------- -----------------------------------
  `institutions`                      `id`, `permanent_id` nullable,
                                      `name`, `normalized_name`, address,
                                      state, region, `group_id`,
                                      verification status

  `institution_aliases`               `id`, `institution_id`, alias,
                                      normalized alias, source,
                                      verification status

  `institution_groups`                `id`, name, group type
                                      (trust/society/other)

  `bureaus`                           `id`, code, name, type, active

  `profiles`                          `id`, display name, active

  `role_assignments`                  `id`, user/profile ID, role, bureau
                                      ID nullable, region ID nullable,
                                      validity/status

  `regions`                           `id`, code, name, parent region ID

  `complaint_cases`                   `id`, `case_ref`, `source_system`,
                                      `source_ref`, `institution_id`
                                      nullable, `institution_name_raw`,
                                      resolution method/confidence,
                                      category, subject, text, language,
                                      status, priority, current bureau,
                                      assigned user, received date, last
                                      action/date, next action, expected
                                      disposal date, restriction flag

  `case_assignments`                  `id`, `case_id`, bureau, officer,
                                      start/end timestamps, actor, reason

  `case_actions`                      `id`, `case_id`, action type,
                                      from/to bureau, actor, timestamp,
                                      remarks, attachment reference,
                                      previous/new state

  `case_links`                        `id`, canonical case pair,
                                      relationship type, state, score,
                                      tier, reasons JSON, scope,
                                      model/config version, decided
                                      by/at, note

  `coordination_notes`                `id`, `link_id`, author, timestamp,
                                      text, proposed/confirmed lead
                                      bureau

  `coordination_actions`              `id`, coordination/link ID, action,
                                      owner, due date, status, timestamps

  `alerts`                            `id`, type, case/link reference,
                                      recipient/scope, created at,
                                      acknowledged by/at

  `sla_rules`                         category, limit days, amber
                                      percentage, active/version

  `evidence_files`                    `id`, case ID, private object key
                                      or local fixture key, metadata,
                                      uploader, verification state

  `audit_logs`                        `id`, actor, action, entity
                                      type/ID, timestamp, structured
                                      change metadata, optional
                                      previous/current hashes

  `system_settings`                   key, value, scope, updated by

  `import_batches`                    id, source, start/end time, counts,
                                      outcome, error summary

  `match_runs` (optional but          id, case ID, configuration/model
  recommended)                        version, run time, candidate count,
                                      result status
  -----------------------------------------------------------------------

### 6.2 Data integrity rules

-   Use immutable primary IDs.
-   Use unique constraints for case IDs and appropriate
    source-system/source-reference combinations.
-   Preserve verified Permanent IDs; allow missing values without
    inventing identifiers.
-   Use foreign keys for institutions, bureaus, users, and cases.
-   Enforce valid statuses, tiers, relationship states, and scopes.
-   Prevent a case from linking to itself.
-   Canonicalize case-pair ordering so the same pair cannot be stored
    twice for the same scope/review version.
-   Index institution ID, status, bureau, received date, expected
    disposal date, external reference, and relationship lookup fields.
-   Use transactions for case creation, transition, link decision, and
    audit event creation.
-   Use idempotency controls for ingestion and background jobs.
-   Keep historical assignments and actions; do not overwrite history to
    show only the current state.
-   Do not routinely delete referenced master data or case records.

### 6.3 Case relationship states

Use: - `suggested` - `linked` - `dismissed` - optionally
`pending_review`

Relationship type may be: - `potential_duplicate` - `related_issue` -
`cross_bureau_overlap` - `group_scope_overlap`

Relationship state is independent of case status.

### 6.4 Audit model

Every important state-changing operation should record: - actor
identity; - action; - entity type and ID; - server timestamp; -
before/after state where applicable; - reason/remarks where required; -
correlation/request ID if available.

An append-only table and restricted database permissions are mandatory
for the prototype. Hash chaining is optional stretch work; do not claim
tamper-proofing unless the implementation and threat model justify that
claim.

## 7. Overlap engine design

### 7.1 Processing pipeline

1.  Normalize incoming source fields in the source adapter.
2.  Resolve institution identity using the L1 priority order.
3.  Persist the canonical case and resolution evidence transactionally.
4.  Select eligible open candidate cases according to the configured
    scope.
5.  Calculate enabled matching signals.
6.  Apply gates and normalized scoring.
7.  Assign tier and produce plain-language reasons.
8.  Persist suggested case links and match-run metadata.
9.  Create an alert only when rules require it, especially for
    cross-cell candidates.
10. Display the stored result in overlap queue, case detail, and
    institution 360.
11. Record human decisions and suppression state.

### 7.2 Candidate eligibility

-   Default: open cases at the same canonical institution.
-   Cross-cell alerts require distinct bureaus/cells.
-   Same-cell candidates may be shown as potential duplicates, clearly
    labelled.
-   Group mode may include sibling campuses with a distinct scope label
    and lower confidence.
-   Region mode is a discovery scope only and must not imply relatedness
    solely from geographic proximity.
-   Restricted-case access rules apply before returning any case
    details.
-   Do not compare closed cases by default for active alerts; allow
    historical lookup in a separate view if needed.

### 7.3 Matching implementation sequence

**First version (P0):** - exact Permanent ID / canonical institution
ID; - normalized name and region; - alias match; - configurable category
compatibility; - temporal proximity and open status; - different-cell
gate; - deterministic score and reasons; - persisted candidates.

Use PostgreSQL with `pg_trgm` where available and Python RapidFuzz for
controlled fuzzy resolution. Keep the exact match and fuzzy resolution
methods distinguishable in stored metadata.

**Second version (P1):** - locally hosted sentence embeddings; -
semantic similarity as an additional signal; - versioned local model and
cached embeddings; - offline load tests.

**Third version (P2):** - multilingual embeddings for Hindi-English
comparison; - group-level overlap refinement.

### 7.4 Matching quality and evaluation

Build a synthetic benchmark with ground-truth case clusters and decoys.
Measure: - precision by tier; - recall across all eligible planted
overlaps; - institution-resolution accuracy; - false-positive rate; -
missed overlap examples; - performance at the chosen dataset size.

Targets from the supplied design are initial MVP goals: - High-tier
precision ≥ 90%; - overall overlap recall ≥ 85%; - institution
resolution accuracy on messy names ≥ 95%; - time to answer "what is
happening to institution X?" ≤ 5 seconds / one screen; - offline demo
path 100%.

These targets are not claims that the system already meets them. Publish
actual benchmark results, including misses, and tune thresholds based on
the synthetic ground truth.

## 8. Technical architecture

### 8.1 Recommended stack

  --------------------------------------------------------------------------
  Layer                   Choice                     Reason
  ----------------------- -------------------------- -----------------------
  Frontend                React + TypeScript + Vite  Fast prototype
                                                     development and
                                                     reusable screens

  Styling/UI              Tailwind CSS or a          Rapid, responsive UI
                          consistent local component 
                          system                     

  Charts                  Recharts or ECharts,       Dashboard
                          locally bundled            visualizations

  Backend                 Python + FastAPI           Typed APIs and
                                                     testability

  Database                PostgreSQL                 Transactions,
                                                     relational integrity,
                                                     indexing

  Fuzzy matching          `pg_trgm` and/or RapidFuzz Explainable institution
                                                     resolution

  Semantic matching       `sentence-transformers`,   Offline semantic signal
                          local model path, optional after P0

  Authentication          Local JWT for offline      No external identity
                          seeded demo users          dependency in demo

  Authorization           Backend RBAC plus query    Defense in depth
                          scoping; database policies 
                          where exposed              

  Background tasks        Lightweight                SLA and matching
                          scheduler/worker           recomputation

  Packaging               Docker Compose plus        Reproducible local
                          start/reset scripts        deployment

  Testing                 Pytest, API tests, DB      Automated verification
                          tests, frontend tests      
  --------------------------------------------------------------------------

**Prototype choice:** use React/Vite rather than adding a Next.js server
unless the team has a specific need for Next.js. The browser should
communicate with FastAPI via an environment-configured or relative API
base URL.

### 8.2 Logical modules

Implement as a modular monolith, not microservices: 1. Identity and
access. 2. Institution registry and resolution. 3. Case intake and
lifecycle. 4. Overlap engine. 5. Coordination. 6. SLA and alerts. 7.
Evidence metadata and access. 8. Audit. 9. Dashboard and reporting. 10.
Source adapters and demo reset.

### 8.3 Simulated source adapters

Implement two mock adapters: - RB-style source schema; - PGRC-style
source schema.

Both map to the same canonical case representation. Adapters should
include sample data with differences in field names, date formats,
institution names, and references to demonstrate normalization. Mark
them as simulated in the UI and documentation.

### 8.4 API conventions

Use `/api/v1` for the backend API.

Illustrative endpoints: - `GET /api/v1/institutions` -
`GET /api/v1/institutions/{id}` -
`GET /api/v1/institutions/{id}/cases` -
`GET /api/v1/institutions/resolve?name=...` - `GET /api/v1/cases` with
filters and pagination - `POST /api/v1/cases` -
`GET /api/v1/cases/{id}` - `GET /api/v1/cases/{id}/history` -
`POST /api/v1/cases/{id}/actions` -
`POST /api/v1/cases/ingest/{source}` -
`GET /api/v1/overlaps?scope=campus|group|region` -
`POST /api/v1/links/{id}/decision` - `GET /api/v1/dashboard/kpis` -
`GET /api/v1/dashboard/workload` - `GET /api/v1/alerts` -
`GET /api/v1/admin/match-quality` - `POST /api/v1/admin/reset-demo`

These are proposed endpoint contracts. Define request/response schemas,
validation, pagination, authorization, and error formats before coding.
Do not trust client-provided role or scope values.

### 8.5 Runtime and portability

-   Entire demo works with no internet after dependencies and any
    optional model are prepared.
-   Bundle fonts, icons, and frontend assets locally.
-   Configure API URL via environment or relative path.
-   Bind services to `0.0.0.0` when LAN access is needed.
-   Test from a second device on the local network.
-   Provide one-command start and reset.
-   Provide health-check endpoint/page.
-   Seed dates relative to demo run time so ageing and SLA states remain
    meaningful.
-   The reset command must clearly warn that it resets synthetic demo
    data only and must not be exposed in production.

## 9. Security, privacy, and governance

### 9.1 Role and scope model

Prototype roles: - `admin` - `officer` - `coordinator` - `bureau_head` -
`regional_officer` - `management` - `auditor`

Authorization must combine role with bureau/region scope. Management and
administrators may have broader views only when explicitly configured.
Administrative capability does not automatically mean unrestricted
access to confidential complaint contents.

### 9.2 Minimum permission rules

-   Officers view and act on cases permitted by assigned bureau/region
    and case restrictions.
-   Coordinators review cross-cell overlap and coordination records
    within authorized scope.
-   Bureau heads see bureau workload and case details within bureau
    scope.
-   Regional officers see records within region scope.
-   Management sees approved cross-cell summaries and permitted detail.
-   Auditors are read-only and scoped.
-   Admins manage configuration and users; sensitive content access is
    separately authorized and audited.

### 9.3 Field masking and restricted cases

-   Complainant identity is visible only to the owning cell or
    explicitly authorized roles.
-   Other cells may see permitted case metadata but not complainant
    identity.
-   Restricted/confidential/sub-judice cases reveal only a minimal
    indicator to unauthorized cells, e.g. "A restricted case exists;
    contact Cell X."
-   Do not include restricted text, attachments, names, or detailed
    matching reasons in unauthorized API responses.
-   Heads-up banners and overlap panels must apply the same restrictions
    as case details.
-   Log all authorized access to restricted details and all decisions
    affecting restricted records.

### 9.4 Technical controls

-   Validate all inputs server-side.
-   Use password hashing and secure local demo authentication practices.
-   Use short-lived tokens and secure secret configuration.
-   Apply rate limiting where appropriate.
-   Protect against SQL injection, XSS, CSRF where applicable, insecure
    direct object references, and privilege escalation.
-   Enforce authorization on every API and evidence operation.
-   Avoid sensitive data in logs.
-   Do not ship production secrets in `.env.example`, source control, or
    frontend bundles.
-   Keep audit records append-only for normal application roles.
-   Use synthetic data only in the prototype.
-   Describe encryption at rest/in transit and formal legal/privacy
    review as production requirements; do not claim regulatory
    compliance solely because the prototype has RBAC.

The DPDP Act 2023 and other applicable requirements need formal legal
and institutional review before production deployment. This PRD does not
constitute a legal compliance certification.

## 10. Non-functional requirements

  -----------------------------------------------------------------------
  Area                                Requirement
  ----------------------------------- -----------------------------------
  Offline                             Complete demo flow works without
                                      internet, CDN, external API, or
                                      runtime model download

  Performance                         Case register and dashboard target
                                      \<2 seconds at approximately 10,000
                                      synthetic cases on declared test
                                      hardware

  Interaction clarity                 Staff can understand
                                      who/what/why/next from an overlap
                                      alert in about 5 seconds

  Reliability                         One-command start/reset and a
                                      health-check page

  Consistency                         State transitions and their audit
                                      events are transactional

  Portability                         Configurable API base URL; local
                                      and second-device LAN test

  Security                            Server-side RBAC, bureau/region
                                      scope, field masking,
                                      restricted-case behavior

  Auditability                        All designated state changes and
                                      decisions are recorded

  Accessibility                       Keyboard access, readable contrast,
                                      labels, responsive layout

  Maintainability                     Versioned migrations, typed API
                                      schemas, automated tests,
                                      documented setup

  Recovery                            Database backup/restore procedure
                                      tested in a separate environment

  Scalability                         Pagination, appropriate indexes,
                                      candidate filtering, and background
                                      jobs for expensive tasks
  -----------------------------------------------------------------------

Performance figures must be measured on documented hardware and test
data. Do not claim production-scale capacity based only on a small local
demo.

## 11. Synthetic dataset and demo fixtures

### 11.1 Dataset scale

Generate and save fixtures before the demo: - 500--2,000 synthetic
institutions; - 5,000--10,000 synthetic cases; - two source schemas (RB
and PGRC); - multiple categories such as fees/refund, faculty,
infrastructure, approval status, admission, and other configurable
categories; - several parent groups/trusts with multiple campuses; -
realistic but fabricated staff and action histories.

Use deterministic seeds so benchmark results and demos can be
reproduced.

### 11.2 Planted ground truth

Include known clusters for: 1. Exact Permanent ID overlap. 2. Messy
institution name / abbreviation overlap. 3. Same institution and
different complaint wording. 4. Same-cell duplicate candidates. 5.
Cross-cell overlap across RB and PGRC. 6. Hindi-English related wording
if multilingual mode is enabled. 7. Cross-campus group-scope candidates.
8. Similar-looking but unrelated decoys. 9. Ambiguous institution
identity that must remain unresolved. 10. Restricted cases that must be
masked for unauthorized roles.

### 11.3 Demo data safeguards

-   Never use actual complainant personal information.
-   Mark the dataset and screens as synthetic/demo.
-   Do not claim the synthetic benchmark represents actual AICTE
    complaint distributions.
-   Keep the running app free of external AI calls.
-   Save generated data and benchmark ground truth in version-controlled
    fixtures, excluding secrets.

## 12. Acceptance criteria and definition of done

### 12.1 P0 acceptance checklist

**Institution identity** - \[ \] Canonical institution and alias records
work. - \[ \] Exact ID resolution takes precedence over fuzzy
matching. - \[ \] Ambiguous records enter unresolved queue. - \[ \]
Resolution method and confidence are visible and persisted. - \[ \]
Institution 360 aggregates permitted cases.

**Case tracking** - \[ \] New cases receive unique IDs. - \[ \] RB and
PGRC adapters normalize into canonical cases. - \[ \] Case register
filters combine correctly. - \[ \] Status transitions are validated
server-side. - \[ \] Assignment, transfer, and case actions are
historized. - \[ \] SLA health and ageing are computed from
configuration. - \[ \] Dashboard KPIs reconcile with database queries.

**Overlap and coordination** - \[ \] Candidate generation runs on
ingest/material update. - \[ \] High/Medium/Info tiers and
plain-language reasons are stored. - \[ \] Cross-cell overlap requires
different cells. - \[ \] Same-cell duplicate suggestions are labelled
distinctly. - \[ \] Link/Not related/Pending actions work. - \[ \]
Dismissed pair suppression works until material change. - \[ \] Linked
cases retain independent identity and history. - \[ \] Coordination
notes and lead-bureau decision are auditable.

**Security** - \[ \] Unauthorized case detail is denied or appropriately
masked. - \[ \] Restricted-case responses do not leak text, identity, or
attachments. - \[ \] Evidence access checks authorization. - \[ \]
Ordinary users cannot edit/delete audit records. - \[ \]
Role/region/bureau filters are enforced server-side.

**Offline and operations** - \[ \] Clean start works using documented
instructions. - \[ \] Reset restores synthetic demo data. - \[ \] Demo
runs with internet disabled. - \[ \] Second-device access is tested if
LAN access is part of the demo. - \[ \] Health check reports service
readiness.

### 12.2 P1/P2 acceptance

-   [ ] Heads-up banner reads stored overlap results.
-   [ ] Match-quality panel reports precision, recall, resolution
    accuracy, false-positive rate, and known misses.
-   [ ] Group scope surfaces sibling-campus candidates with a distinct
    label.
-   [ ] Semantic matching loads only from a local model path and has a
    deterministic fallback.
-   [ ] Multilingual matching is demonstrated offline before it is
    considered complete.

### 12.3 Test strategy

-   Unit tests: normalization, institution resolution, scoring, tiers,
    SLA calculations, transition rules.
-   Database tests: constraints, indexes, transaction behavior,
    authorization policies.
-   API tests: schemas, filters, error responses, access restrictions.
-   Integration tests: source ingest → resolve institution → create case
    → calculate overlap → review link → dashboard update.
-   Frontend tests: register filters, case details, overlap review,
    banners, alerts, empty/error states.
-   Security tests: ID manipulation, privilege escalation,
    restricted-case leakage, evidence access.
-   Performance tests: dashboard and register at 10,000 synthetic cases;
    matching throughput.
-   Recovery tests: restart, failed jobs, backup/restore.
-   End-to-end tests: full demo script.

## 13. Three-minute demo script

**Scene 1 --- Institution 360** Open a synthetic institution with two
open cases from different cells. Show the institution identity and
consolidated case history.

**Scene 2 --- Messy incoming complaint** Simulate a new RB- or
PGRC-style source record with a misspelled institution name. Show safe
resolution to the canonical institution and its stored
method/confidence.

**Scene 3 --- Explainable overlap** Show the alert with case IDs,
bureaus, tier, score, and reasons. Explain why the platform recommends
review without claiming the cases are identical.

**Scene 4 --- Heads-up banner and coordination room** Open case detail,
show the other-cell banner, link the cases, propose RB as lead, and add
a timestamped note.

**Scene 5 --- Optional semantic/group capability** If validated and
available offline, show a differently worded complaint matched by
semantic similarity, or switch group scope to show sibling-campus cases.
Skip if the optional capability is not stable.

**Scene 6 --- SLA and workload** Show a case past its configured
synthetic deadline, the beyond-timeline queue, and bureau workload.

**Scene 7 --- Match-quality panel** Show measured precision/recall and
known misses from planted ground truth. State clearly that results are
synthetic and real-world calibration requires an authorized pilot.

## 14. Risks and mitigations

  -----------------------------------------------------------------------
  Risk                    Impact                  Mitigation
  ----------------------- ----------------------- -----------------------
  Too many features,      High                    Complete L1--L4 and
  incomplete core                                 coordination loop
                                                  before optional AI

  False positives         Medium/High             Tiers, readable
  overwhelm staff                                 reasons, dismissal
                                                  suppression, quality
                                                  panel

  Institution             High                    ID-first resolution,
  mis-resolution                                  ambiguity queue,
                                                  provenance

  Offline embedding model Medium/High             Preload locally, test
  fails                                           in airplane mode,
                                                  deterministic fallback

  No real data available  Medium                  Planted ground truth,
                                                  honest benchmark,
                                                  synthetic disclaimer

  Restricted data leaks   High                    Shared
  via alerts                                      authorization/masking
                                                  layer for all responses

  Hardcoded localhost     Medium                  Configurable API URL,
  prevents LAN demo                               `0.0.0.0`,
                                                  second-device test

  Dashboard counts are    High                    Metric definitions and
  misleading                                      database reconciliation
                                                  tests

  Source integration      Medium                  Explicit simulated
  unavailable                                     adapter boundary

  Policy differs from     High                    Configurable rules and
  assumed workflow                                stakeholder validation

  Regulator structure     Low/Medium              Bureaus and source
  changes                                         systems modeled as data

  Scope creep             High                    P0/P1/P2 cut line and
                                                  acceptance gates
  -----------------------------------------------------------------------

## 15. Implementation roadmap

Estimates are illustrative for a small, focused team and should be
adapted to actual team size and deadline.

### Phase 0 --- Freeze scope and UX

-   Confirm role matrix, case states, field list, SLA defaults, and demo
    stories.
-   Create wireframes for dashboard, register, case detail, Institution
    360, overlap review, and coordination.
-   Record unresolved policy assumptions.

**Exit gate:** screen map, data dictionary, and acceptance criteria
agreed.

### Phase 1 --- Foundation

-   Set up React/Vite frontend, FastAPI backend, PostgreSQL, Docker
    Compose.
-   Add migrations, seeded local auth, role/bureau/region scope.
-   Create institution, aliases, bureaus, profiles, and case schema.
-   Add synthetic fixtures and health check.

**Exit gate:** app starts cleanly and database/security tests pass.

### Phase 2 --- L1 and L4 foundations

-   Institution search and Institution 360.
-   Case register, case detail, filters, status timeline.
-   RB/PGRC simulated source adapters.
-   Initial dashboard with persisted-data KPIs.

**Exit gate:** users can trace cases for one institution.

### Phase 3 --- L2 overlap engine

-   Implement institution resolution, candidate selection, configurable
    scoring, reasons, tiers, and persistence.
-   Add candidate review queue.
-   Test planted true overlaps and decoys.

**Exit gate:** overlap results are explainable and reproducible.

### Phase 4 --- L3 coordination

-   Link/dismiss/pending decisions.
-   Dismissal suppression.
-   Lead bureau and notes.
-   Link/unlink audit events.
-   Heads-up banner if core loop is stable.

**Exit gate:** Identify → Detect → Explain → Coordinate → Track works
end to end.

### Phase 5 --- SLA, alerts, and exports

-   Configurable SLA rules, ageing, alert list, acknowledgement.
-   Filtered CSV export and optional PDF.
-   Verify KPI reconciliation.

**Exit gate:** overdue scenario is repeatable on demo day.

### Phase 6 --- Hardening and evaluator evidence

-   Security and negative tests.
-   Offline/airplane-mode test.
-   10,000-case performance test.
-   Backup/restore rehearsal.
-   Match-quality report and demo script.

**Exit gate:** all critical P0 tests pass.

### Phase 7 --- Optional differentiators

-   Group scope.
-   Local semantic embeddings.
-   Multilingual matching.
-   Richer analytics.

Only start a feature if the core loop is stable and the remaining time
supports testing it.

## 16. Repository structure

``` text
institutionwatch/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   │   ├── dashboard/
│   │   │   ├── institutions/
│   │   │   ├── cases/
│   │   │   ├── overlaps/
│   │   │   ├── coordination/
│   │   │   ├── alerts/
│   │   │   └── admin/
│   │   ├── api/
│   │   └── types/
│   └── tests/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── institution_resolution.py
│   │   │   ├── overlap_engine.py
│   │   │   ├── coordination.py
│   │   │   ├── sla.py
│   │   │   └── audit.py
│   │   ├── adapters/
│   │   │   ├── rb_mock.py
│   │   │   └── pgrc_mock.py
│   │   └── workers/
│   └── tests/
├── db/
│   ├── migrations/
│   ├── seed/
│   └── tests/
├── benchmark/
│   ├── ground_truth/
│   ├── generate_data.py
│   └── evaluate_matching.py
├── docs/
│   ├── ULTIMATE_PRD.md
│   ├── architecture.md
│   ├── data_dictionary.md
│   ├── security_model.md
│   ├── api_contracts.md
│   └── demo_script.md
├── scripts/
│   ├── start_demo
│   ├── reset_demo
│   └── health_check
├── docker-compose.yml
├── .env.example
└── README.md
```

This is a recommended structure, not a mandate to create every file
before the first vertical slice. Keep code modular and create files as
their functionality is implemented.

## 17. Required prototype deliverables

1.  Working offline-first web application.
2.  FastAPI backend with versioned endpoints.
3.  PostgreSQL schema and migrations.
4.  RB and PGRC simulated source adapters.
5.  Synthetic institution/case dataset and planted ground truth.
6.  Institution identity resolution and Institution 360.
7.  Explainable overlap engine with persisted results.
8.  Coordination room and decision history.
9.  Dashboard, case register, SLA/ageing, and alerts.
10. RBAC and restricted-case masking tests.
11. Match-quality evaluation output.
12. One-command start/reset instructions.
13. Setup, architecture, data dictionary, and API documentation.
14. Three-minute demo script and known-limitations statement.

## 18. Open decisions before production

The prototype may use the defaults above, but the following must be
confirmed before real deployment: 1. Official Permanent ID format and
source-system identifiers. 2. Real RB/PGRC/CPGRAMS interface contracts
and authorization. 3. Approved complaint categories and related-category
mapping. 4. Official category-specific SLA rules, holidays, and
pause/resume policy. 5. Who may decide the lead bureau when cells
disagree. 6. Whether same-cell duplicate handling requires additional
review or a separate workflow. 7. Rules for confidential and sub-judice
records. 8. Data retention, archival, deletion, and access-review
procedures. 9. Whether external AI processing is permitted. 10.
Production identity provider, hosting, monitoring, backup, and incident
response requirements.

## 19. Final prototype decision

**Build InstitutionWatch as a local-first, modular React/Vite +
FastAPI + PostgreSQL application.** The first successful milestone is
not an advanced AI dashboard; it is a complete and secure cross-bureau
workflow:

**Register → Resolve institution → Detect overlap → Explain match →
Human coordination decision → Track status/SLA → Audit and report.**

P0 completion means L1--L4, simulated source ingestion, the coordination
room, basic security/masking, synthetic evaluation fixtures, and a
repeatable offline demo all work together. L5, L6, L7, and the
match-quality add-on should be added only after the core loop passes its
tests.

The product's strongest evaluation story is not "we use AI." It is: **we
connect fragmented cases, explain potential overlap, preserve human
authority, and measure whether the matching works.**

------------------------------------------------------------------------
