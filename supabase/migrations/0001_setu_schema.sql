-- SETU PS26264 — Initial schema migration
-- All imported records are synthetic demo data.

create extension if not exists pg_trgm;

-- 1. Dataset metadata
create table if not exists public.setu_dataset_manifest (
    dataset_id text primary key,
    manifest jsonb not null
);

-- 2. Reference tables
create table if not exists public.regions (
    region_id text primary key,
    state text not null,
    district text,
    region_type text
);

create table if not exists public.institution_groups (
    group_id text primary key,
    name text not null,
    group_type text
);

create table if not exists public.bureaus (
    bureau_id text primary key,
    name text not null,
    type text
);

-- 3. Institution identity
create table if not exists public.institutions (
    institution_id text primary key,
    permanent_id text,
    name text not null,
    normalized_name text,
    address text,
    state text,
    district text,
    region_id text references public.regions(region_id),
    group_id text references public.institution_groups(group_id),
    campus_number integer,
    is_synthetic boolean not null default true
);

create table if not exists public.institution_aliases (
    alias_id text primary key,
    institution_id text not null
        references public.institutions(institution_id),
    alias text not null,
    alias_type text,
    is_synthetic boolean not null default true
);

-- 4. Synthetic demo profiles.
-- These are not Supabase Auth identities.
create table if not exists public.profiles (
    user_id text primary key,
    display_name text,
    role text,
    bureau_id text references public.bureaus(bureau_id),
    region_id text references public.regions(region_id),
    is_synthetic boolean not null default true,
    demo_only boolean not null default true
);

-- 5. Main complaint records
create table if not exists public.complaint_cases (
    case_id text primary key,
    case_ref text unique,
    source_system text,
    source_ref text,
    institution_id text references public.institutions(institution_id),
    institution_name_raw text,
    permanent_id_raw text,
    resolution_method text,
    resolution_confidence numeric,
    resolution_status text,
    category text,
    issue_key_synthetic text,
    "text" text,
    language text,
    status text,
    current_bureau_id text references public.bureaus(bureau_id),
    assigned_user_id text references public.profiles(user_id),
    received_date date,
    last_action text,
    last_action_date date,
    next_action text,
    expected_disposal_date date,
    sla_limit_days integer,
    ageing_days integer,
    ageing_bucket text,
    sla_elapsed_pct numeric,
    sla_state text,
    is_restricted boolean not null default false,
    restricted_visibility text,
    group_id text references public.institution_groups(group_id),
    state text,
    district text,
    region_id text references public.regions(region_id),
    cluster_id text,
    ground_truth_role text,
    is_same_cell_duplicate boolean not null default false,
    is_synthetic boolean not null default true
);

-- 6. Case activity history
create table if not exists public.case_actions (
    action_id text primary key,
    case_id text not null
        references public.complaint_cases(case_id),
    action_type text,
    from_bureau_id text references public.bureaus(bureau_id),
    to_bureau_id text references public.bureaus(bureau_id),
    actor_user_id text references public.profiles(user_id),
    "timestamp" timestamptz,
    remarks text,
    attachment_ref text,
    is_synthetic boolean not null default true
);

-- 7. Cross-case links and coordination
create table if not exists public.case_links (
    link_id text primary key,
    case_a text not null references public.complaint_cases(case_id),
    case_b text not null references public.complaint_cases(case_id),
    state text,
    score numeric,
    tier text,
    reasons jsonb,
    scope text,
    decided_by text references public.profiles(user_id),
    decided_at timestamptz,
    note text,
    cluster_id text,
    is_synthetic boolean not null default true,
    check (case_a <> case_b)
);

create table if not exists public.coordination_notes (
    note_id text primary key,
    link_id text not null references public.case_links(link_id),
    author_user_id text references public.profiles(user_id),
    "timestamp" timestamptz,
    "text" text,
    proposed_lead_bureau_id text references public.bureaus(bureau_id),
    is_synthetic boolean not null default true
);

-- 8. Alerts
create table if not exists public.alerts (
    alert_id text primary key,
    alert_type text,
    case_id text references public.complaint_cases(case_id),
    link_id text references public.case_links(link_id),
    created_at timestamptz,
    acknowledged_by text references public.profiles(user_id),
    status text,
    is_synthetic boolean not null default true
);

-- 9. SLA configuration
create table if not exists public.sla_rules (
    category text primary key,
    limit_days integer not null,
    amber_pct numeric,
    red_when_breached boolean,
    is_synthetic_config boolean not null default true
);

-- 10. Audit history
create table if not exists public.audit_logs (
    audit_id text primary key,
    "timestamp" timestamptz,
    actor_user_id text references public.profiles(user_id),
    action text,
    entity_type text,
    entity_id text,
    details jsonb,
    is_synthetic boolean not null default true
);

-- 11. Evaluation ground truth
create table if not exists public.ground_truth_pairs (
    pair_id text primary key,
    case_a text not null references public.complaint_cases(case_id),
    case_b text not null references public.complaint_cases(case_id),
    is_true_overlap boolean not null,
    overlap_type text,
    required_scope text,
    cluster_id text,
    expected_signal text,
    expected_cross_bureau boolean,
    is_synthetic boolean not null default true,
    check (case_a <> case_b)
);

create table if not exists public.ground_truth_clusters (
    cluster_id text primary key,
    cluster_type text,
    issue_key text,
    case_ids jsonb,
    institution_ids jsonb,
    expected_behavior text
);

create table if not exists public.institution_resolution_ground_truth (
    test_id text primary key,
    raw_name text,
    raw_permanent_id text,
    state text,
    district text,
    expected_institution_id text
        references public.institutions(institution_id),
    expected_resolution_method text,
    expected_confidence_min numeric,
    expected_status text,
    scenario text,
    is_synthetic boolean not null default true
);

-- 12. Query indexes
create index if not exists idx_institutions_normalized_name
    on public.institutions using gin (normalized_name gin_trgm_ops);

create index if not exists idx_institutions_permanent_id
    on public.institutions (permanent_id);

create index if not exists idx_aliases_institution
    on public.institution_aliases (institution_id);

create index if not exists idx_aliases_alias
    on public.institution_aliases using gin (alias gin_trgm_ops);

create index if not exists idx_cases_institution
    on public.complaint_cases (institution_id);

create index if not exists idx_cases_bureau_status
    on public.complaint_cases (current_bureau_id, status);

create index if not exists idx_cases_received_date
    on public.complaint_cases (received_date);

create index if not exists idx_actions_case_timestamp
    on public.case_actions (case_id, "timestamp");

create index if not exists idx_case_links_case_a
    on public.case_links (case_a);

create index if not exists idx_case_links_case_b
    on public.case_links (case_b);

create index if not exists idx_alerts_case_status
    on public.alerts (case_id, status);