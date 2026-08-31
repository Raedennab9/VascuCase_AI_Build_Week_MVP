begin;

create schema if not exists private;

revoke all on schema private from public, anon, authenticated, service_role;
grant usage on schema private to service_role;

create table public.vascucase_participants (
    participant_id uuid primary key default gen_random_uuid(),
    name text not null,
    email text not null unique,
    training_level text not null,
    institution text not null,
    institution_number text,
    consent_given boolean not null,
    consent_version text not null,
    consented_at timestamptz not null default now(),
    registered_at timestamptz not null default now(),
    constraint vascucase_participants_name_length_check
        check (char_length(btrim(name)) between 2 and 120),
    constraint vascucase_participants_email_normalized_check
        check (
            char_length(email) between 3 and 254
            and email = lower(btrim(email))
        ),
    constraint vascucase_participants_training_level_check
        check (training_level in (
            'Medical student',
            'Surgical resident',
            'Vascular trainee'
        )),
    constraint vascucase_participants_institution_normalized_check
        check (
            char_length(institution) > 0
            and institution = regexp_replace(
                btrim(institution),
                '[[:space:]]+',
                ' ',
                'g'
            )
        ),
    constraint vascucase_participants_institution_number_trimmed_check
        check (
            institution_number is null
            or (
                char_length(institution_number) > 0
                and institution_number = regexp_replace(
                    regexp_replace(
                        institution_number,
                        '^[[:space:]]+',
                        '',
                        'g'
                    ),
                    '[[:space:]]+$',
                    '',
                    'g'
                )
            )
        ),
    constraint vascucase_participants_student_number_required_check
        check (
            training_level <> 'Medical student'
            or institution_number is not null
        ),
    constraint vascucase_participants_consent_given_check
        check (consent_given is true),
    constraint vascucase_participants_consent_version_check
        check (consent_version = 'vascucase-data-use-v1')
);

-- The email UNIQUE constraint also creates its B-tree index.

create table public.case_results (
    result_id uuid primary key default gen_random_uuid(),
    participant_id uuid not null
        references public.vascucase_participants(participant_id)
        on delete cascade,
    case_id text not null,
    case_version text not null,
    case_name text not null,
    score integer not null,
    max_score integer not null,
    percentage numeric(5, 2) generated always as (
        round((score::numeric * 100) / max_score::numeric, 2)
    ) stored,
    attempt_number integer not null,
    version_attempt_number integer not null,
    completed_at timestamptz not null default now(),
    constraint case_results_case_id_length_check
        check (char_length(btrim(case_id)) between 1 and 100),
    constraint case_results_case_version_nonempty_check
        check (btrim(case_version) <> ''),
    constraint case_results_case_name_length_check
        check (char_length(btrim(case_name)) between 1 and 240),
    constraint case_results_score_check
        check (score >= 0 and max_score > 0 and score <= max_score),
    constraint case_results_percentage_check
        check (percentage >= 0 and percentage <= 100),
    constraint case_results_attempt_number_check
        check (attempt_number > 0),
    constraint case_results_version_attempt_number_check
        check (version_attempt_number > 0),
    constraint case_results_participant_case_attempt_unique
        unique (participant_id, case_id, attempt_number),
    constraint case_results_participant_case_version_attempt_unique
        unique (
            participant_id,
            case_id,
            case_version,
            version_attempt_number
        )
);

create index case_results_participant_id_idx
    on public.case_results (participant_id);
create index case_results_case_id_idx
    on public.case_results (case_id);
create index case_results_completed_at_idx
    on public.case_results (completed_at desc);

alter table public.vascucase_participants enable row level security;
alter table public.case_results enable row level security;

-- There are intentionally no table policies. The app can only use the
-- service-role-only RPC wrappers below; raw table operations stay unavailable.
revoke all on table
    public.vascucase_participants,
    public.case_results
from public, anon, authenticated, service_role;

create or replace function private.register_vascucase_participant(
    p_name text,
    p_email text,
    p_training_level text,
    p_institution text,
    p_institution_number text,
    p_consent_given boolean,
    p_consent_version text
)
returns public.vascucase_participants
language plpgsql
security definer
set search_path = ''
as $$
declare
    v_name text := btrim(
        regexp_replace(p_name, '[[:space:]]+', ' ', 'g')
    );
    v_email text := lower(btrim(p_email));
    v_training_level text := btrim(p_training_level);
    v_institution text := btrim(
        regexp_replace(p_institution, '[[:space:]]+', ' ', 'g')
    );
    v_institution_number text := nullif(
        regexp_replace(
            regexp_replace(
                p_institution_number,
                '^[[:space:]]+',
                '',
                'g'
            ),
            '[[:space:]]+$',
            '',
            'g'
        ),
        ''
    );
    v_consent_version text := btrim(p_consent_version);
    v_participant public.vascucase_participants%rowtype;
begin
    if p_name is null or char_length(v_name) not between 2 and 120 then
        raise exception 'name must contain between 2 and 120 characters'
            using errcode = '23514';
    end if;

    if p_email is null or char_length(v_email) not between 3 and 254 then
        raise exception 'email must contain between 3 and 254 characters'
            using errcode = '23514';
    end if;

    if v_training_level is null or v_training_level not in (
        'Medical student',
        'Surgical resident',
        'Vascular trainee'
    ) then
        raise exception 'invalid training level' using errcode = '23514';
    end if;

    if p_institution is null or v_institution = '' then
        raise exception 'institution is required'
            using errcode = '23514';
    end if;

    if v_training_level = 'Medical student'
       and v_institution_number is null then
        raise exception 'institution number is required for medical students'
            using errcode = '23514';
    end if;

    if p_consent_given is not true then
        raise exception 'privacy consent is required' using errcode = '23514';
    end if;

    if v_consent_version is distinct from 'vascucase-data-use-v1' then
        raise exception 'current consent version is required'
            using errcode = '23514';
    end if;

    insert into public.vascucase_participants (
        name,
        email,
        training_level,
        institution,
        institution_number,
        consent_given,
        consent_version
    )
    values (
        v_name,
        v_email,
        v_training_level,
        v_institution,
        v_institution_number,
        true,
        v_consent_version
    )
    on conflict (email) do nothing
    returning * into v_participant;

    if found then
        return v_participant;
    end if;

    select participant.*
    into v_participant
    from public.vascucase_participants as participant
    where participant.email = v_email
    for update;

    if not found then
        raise exception 'registration could not be completed with the submitted details'
            using errcode = '23505';
    end if;

    if v_participant.name is distinct from v_name
       or v_participant.email is distinct from v_email
       or v_participant.training_level is distinct from v_training_level
       or v_participant.institution is distinct from v_institution
       or v_participant.institution_number is distinct from v_institution_number
       or v_participant.consent_given is distinct from true
       or v_participant.consent_version is distinct from v_consent_version then
        raise exception 'registration could not be completed with the submitted details'
            using errcode = '23505';
    end if;

    return v_participant;
end;
$$;

create or replace function private.save_vascucase_result(
    p_participant_id uuid,
    p_case_id text,
    p_case_version text,
    p_case_name text,
    p_score integer,
    p_max_score integer,
    p_result_id uuid default gen_random_uuid()
)
returns public.case_results
language plpgsql
security definer
set search_path = ''
as $$
declare
    v_result_id uuid := coalesce(p_result_id, gen_random_uuid());
    v_case_id text := btrim(p_case_id);
    v_case_version text := btrim(p_case_version);
    v_case_name text := btrim(
        regexp_replace(p_case_name, '[[:space:]]+', ' ', 'g')
    );
    v_attempt_number integer;
    v_version_attempt_number integer;
    v_existing public.case_results%rowtype;
    v_result public.case_results%rowtype;
begin
    if p_participant_id is null then
        raise exception 'participant identifier is required'
            using errcode = '23502';
    end if;

    if p_case_id is null or char_length(v_case_id) not between 1 and 100 then
        raise exception 'case identifier must contain between 1 and 100 characters'
            using errcode = '23514';
    end if;

    if p_case_version is null or v_case_version = '' then
        raise exception 'case version is required' using errcode = '23514';
    end if;

    if p_case_name is null
       or char_length(v_case_name) not between 1 and 240 then
        raise exception 'case name must contain between 1 and 240 characters'
            using errcode = '23514';
    end if;

    if p_score is null or p_max_score is null
       or p_score < 0 or p_max_score <= 0 or p_score > p_max_score then
        raise exception 'invalid score' using errcode = '23514';
    end if;

    -- One participant-row lock serializes both attempt sequences and makes a
    -- retry with the same result UUID safe under concurrent requests.
    perform 1
    from public.vascucase_participants as participant
    where participant.participant_id = p_participant_id
    for update;

    if not found then
        raise exception 'registered participant does not exist'
            using errcode = '23503';
    end if;

    select result.*
    into v_existing
    from public.case_results as result
    where result.result_id = v_result_id;

    if found then
        if v_existing.participant_id is distinct from p_participant_id
           or v_existing.case_id is distinct from v_case_id
           or v_existing.case_version is distinct from v_case_version
           or v_existing.score is distinct from p_score
           or v_existing.max_score is distinct from p_max_score then
            raise exception 'result identifier conflicts with another completion'
                using errcode = '23505';
        end if;

        -- completed_at is deliberately excluded from retry identity. A retry
        -- always returns the timestamp stored by the first committed write.
        return v_existing;
    end if;

    select coalesce(max(attempt_number), 0) + 1
    into v_attempt_number
    from public.case_results
    where participant_id = p_participant_id
      and case_id = v_case_id;

    select coalesce(max(version_attempt_number), 0) + 1
    into v_version_attempt_number
    from public.case_results
    where participant_id = p_participant_id
      and case_id = v_case_id
      and case_version = v_case_version;

    insert into public.case_results (
        result_id,
        participant_id,
        case_id,
        case_version,
        case_name,
        score,
        max_score,
        attempt_number,
        version_attempt_number
    )
    values (
        v_result_id,
        p_participant_id,
        v_case_id,
        v_case_version,
        v_case_name,
        p_score,
        p_max_score,
        v_attempt_number,
        v_version_attempt_number
    )
    returning * into v_result;

    return v_result;
end;
$$;

create or replace function public.register_vascucase_participant(
    p_name text,
    p_email text,
    p_training_level text,
    p_institution text,
    p_institution_number text,
    p_consent_given boolean,
    p_consent_version text
)
returns public.vascucase_participants
language plpgsql
security invoker
set search_path = ''
as $$
begin
    return private.register_vascucase_participant(
        p_name,
        p_email,
        p_training_level,
        p_institution,
        p_institution_number,
        p_consent_given,
        p_consent_version
    );
end;
$$;

create or replace function public.save_vascucase_result(
    p_participant_id uuid,
    p_case_id text,
    p_case_version text,
    p_case_name text,
    p_score integer,
    p_max_score integer,
    p_result_id uuid default gen_random_uuid()
)
returns public.case_results
language plpgsql
security invoker
set search_path = ''
as $$
begin
    return private.save_vascucase_result(
        p_participant_id,
        p_case_id,
        p_case_version,
        p_case_name,
        p_score,
        p_max_score,
        p_result_id
    );
end;
$$;

revoke all on function private.register_vascucase_participant(
    text, text, text, text, text, boolean, text
)
    from public, anon, authenticated, service_role;
revoke all on function private.save_vascucase_result(
    uuid, text, text, text, integer, integer, uuid
)
    from public, anon, authenticated, service_role;

revoke all on function public.register_vascucase_participant(
    text, text, text, text, text, boolean, text
)
    from public, anon, authenticated, service_role;
revoke all on function public.save_vascucase_result(
    uuid, text, text, text, integer, integer, uuid
)
    from public, anon, authenticated, service_role;

grant execute on function private.register_vascucase_participant(
    text, text, text, text, text, boolean, text
)
    to service_role;
grant execute on function private.save_vascucase_result(
    uuid, text, text, text, integer, integer, uuid
)
    to service_role;

grant execute on function public.register_vascucase_participant(
    text, text, text, text, text, boolean, text
)
    to service_role;
grant execute on function public.save_vascucase_result(
    uuid, text, text, text, integer, integer, uuid
)
    to service_role;

notify pgrst, 'reload schema';

commit;
