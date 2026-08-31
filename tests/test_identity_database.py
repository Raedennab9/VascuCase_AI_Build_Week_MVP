from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from vascucase import database
from vascucase.cases import CASES
from vascucase.cases.library import LEARNER_LEVELS
from tests.fake_database import FakeDatabase


class RecordingSupabaseClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls: list[tuple[str, dict[str, object]]] = []

    def rpc(self, function_name, params):
        self.calls.append((function_name, dict(params)))
        return RecordingRequest(self)


class RecordingRequest:
    def __init__(self, client):
        self.client = client

    def execute(self):
        response = self.client.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return SimpleNamespace(data=response)


def _participant_row(
    *,
    participant_id=None,
    name="Alex Morgan",
    email="alex@example.com",
    training_level="Medical student",
    institution="Yarmouk University",
    institution_number="00127",
    consented_at="2026-08-31T09:00:00+00:00",
    registered_at="2026-08-31T09:00:00+00:00",
):
    return {
        "participant_id": str(participant_id or uuid4()),
        "name": name,
        "email": email,
        "training_level": training_level,
        "institution": institution,
        "institution_number": institution_number,
        "consent_given": True,
        "consent_version": database.CONSENT_VERSION,
        "consented_at": consented_at,
        "registered_at": registered_at,
    }


def _result_row(
    *,
    result_id,
    participant_id,
    case_version="1",
    attempt_number=3,
    version_attempt_number=2,
):
    return {
        "result_id": str(result_id),
        "participant_id": str(participant_id),
        "case_id": "case-1",
        "case_name": "Case One",
        "case_version": case_version,
        "score": 37,
        "max_score": 50,
        "percentage": "74.00",
        "attempt_number": attempt_number,
        "version_attempt_number": version_attempt_number,
        "completed_at": "2026-08-31T10:30:00+00:00",
    }


def test_register_participant_normalizes_profile_and_calls_atomic_rpc():
    participant_id = uuid4()
    client = RecordingSupabaseClient(
        [[_participant_row(participant_id=participant_id)]]
    )

    participant = database.register_participant(
        client=client,
        name="  Alex   Morgan ",
        email=" Alex@Example.COM ",
        training_level="Medical student",
        institution="  Yarmouk    University  ",
        institution_number="  00127  ",
        consent_given=True,
        consent_version=database.CONSENT_VERSION,
    )

    assert participant.participant_id == participant_id
    assert participant.email == "alex@example.com"
    assert participant.institution == "Yarmouk University"
    assert participant.institution_number == "00127"
    assert participant.consented_at == datetime(
        2026, 8, 31, 9, 0, tzinfo=timezone.utc
    )
    assert client.calls == [
        (
            "register_vascucase_participant",
            {
                "p_name": "Alex Morgan",
                "p_email": "alex@example.com",
                "p_training_level": "Medical student",
                "p_institution": "Yarmouk University",
                "p_institution_number": "00127",
                "p_consent_given": True,
                "p_consent_version": database.CONSENT_VERSION,
            },
        )
    ]


def test_exact_duplicate_response_reuses_participant_id_and_timestamps():
    participant_id = uuid4()
    row = _participant_row(participant_id=participant_id)
    client = RecordingSupabaseClient([[row], [row]])
    kwargs = {
        "client": client,
        "name": "Alex Morgan",
        "email": "ALEX@example.com",
        "training_level": "Medical student",
        "institution": "Yarmouk University",
        "institution_number": "00127",
        "consent_given": True,
        "consent_version": database.CONSENT_VERSION,
    }

    first = database.register_participant(**kwargs)
    second = database.register_participant(**kwargs)

    assert second.participant_id == first.participant_id == participant_id
    assert second.registered_at == first.registered_at
    assert second.consented_at == first.consented_at
    assert client.calls[0] == client.calls[1]


@pytest.mark.parametrize("institution_number", [None, "", "   "])
def test_medical_student_requires_nonempty_institution_number(
    institution_number,
):
    client = RecordingSupabaseClient([])

    with pytest.raises(ValueError, match="(?i)institution number"):
        database.register_participant(
            client=client,
            name="Alex Morgan",
            email="alex@example.com",
            training_level="Medical student",
            institution="Yarmouk University",
            institution_number=institution_number,
            consent_given=True,
            consent_version=database.CONSENT_VERSION,
        )

    assert client.calls == []


@pytest.mark.parametrize(
    ("training_level", "institution_number", "expected"),
    [
        ("Surgical resident", None, None),
        ("Surgical resident", "   ", None),
        ("Vascular trainee", "  00 A-17  ", "00 A-17"),
    ],
)
def test_nonstudents_may_omit_number_and_characters_are_preserved(
    training_level,
    institution_number,
    expected,
):
    row = _participant_row(
        training_level=training_level,
        institution_number=expected,
    )
    client = RecordingSupabaseClient([[row]])

    participant = database.register_participant(
        client=client,
        name="Alex Morgan",
        email="alex@example.com",
        training_level=training_level,
        institution="Yarmouk University",
        institution_number=institution_number,
        consent_given=True,
        consent_version=database.CONSENT_VERSION,
    )

    assert participant.institution_number == expected
    assert client.calls[0][1]["p_institution_number"] == expected


def test_missing_or_stale_consent_is_rejected_before_database_access():
    client = RecordingSupabaseClient([])
    base = {
        "client": client,
        "name": "Alex Morgan",
        "email": "alex@example.com",
        "training_level": "Surgical resident",
        "institution": "Yarmouk University",
        "institution_number": None,
    }

    with pytest.raises(ValueError, match="consent"):
        database.register_participant(
            **base,
            consent_given=False,
            consent_version=database.CONSENT_VERSION,
        )
    with pytest.raises(ValueError):
        database.register_participant(
            **base,
            consent_given=True,
            consent_version="obsolete",
        )

    assert client.calls == []


def test_save_result_sends_participant_id_case_version_and_maps_attempts():
    participant_id = uuid4()
    result_id = uuid4()
    client = RecordingSupabaseClient(
        [[_result_row(result_id=result_id, participant_id=participant_id)]]
    )

    stored = database.save_case_result(
        client=client,
        result_id=result_id,
        participant_id=participant_id,
        case_id="case-1",
        case_name="Case One",
        case_version="1",
        score=37,
        max_score=50,
    )

    assert stored.participant_id == participant_id
    assert stored.percentage == Decimal("74.00")
    assert (stored.attempt_number, stored.version_attempt_number) == (3, 2)
    assert client.calls == [
        (
            "save_vascucase_result",
            {
                "p_participant_id": str(participant_id),
                "p_case_id": "case-1",
                "p_case_name": "Case One",
                "p_case_version": "1",
                "p_score": 37,
                "p_max_score": 50,
                "p_result_id": str(result_id),
            },
        )
    ]


def test_result_retry_reuses_stable_id_payload_and_attempt_numbers():
    participant_id = uuid4()
    result_id = uuid4()
    row = _result_row(
        result_id=result_id,
        participant_id=participant_id,
        attempt_number=1,
        version_attempt_number=1,
    )
    client = RecordingSupabaseClient([[row], [row]])
    kwargs = {
        "client": client,
        "result_id": result_id,
        "participant_id": participant_id,
        "case_id": "case-1",
        "case_name": "Case One",
        "case_version": "1",
        "score": 37,
        "max_score": 50,
    }

    first = database.save_case_result(**kwargs)
    second = database.save_case_result(**kwargs)

    assert first == second
    assert (second.attempt_number, second.version_attempt_number) == (1, 1)
    assert client.calls[0] == client.calls[1]


def test_result_retry_accepts_the_original_stored_case_name():
    participant_id = uuid4()
    result_id = uuid4()
    row = _result_row(result_id=result_id, participant_id=participant_id)
    client = RecordingSupabaseClient([[row]])

    stored = database.save_case_result(
        client=client,
        result_id=result_id,
        participant_id=participant_id,
        case_id="case-1",
        case_name="Renamed Case One",
        case_version="1",
        score=37,
        max_score=50,
    )

    assert stored.case_name == "Case One"
    assert (stored.attempt_number, stored.version_attempt_number) == (3, 2)


def test_fake_store_counts_overall_attempts_across_versions_and_per_version():
    fake = FakeDatabase()
    participant = fake.seed_participant()

    def save(version):
        return fake.save_case_result(
            client=fake.client,
            result_id=uuid4(),
            participant_id=participant.participant_id,
            case_id="case-1",
            case_name="Case One",
            case_version=version,
            score=40,
            max_score=50,
        )

    first_v1 = save("1")
    second_v1 = save("1")
    first_v2 = save("2")
    third_v1 = save("1")

    assert [
        (item.attempt_number, item.version_attempt_number)
        for item in (first_v1, second_v1, first_v2, third_v1)
    ] == [(1, 1), (2, 2), (3, 1), (4, 3)]


def test_fake_store_ambiguous_retry_does_not_create_second_attempt():
    fake = FakeDatabase()
    participant = fake.seed_participant()
    result_id = uuid4()
    kwargs = {
        "client": fake.client,
        "result_id": result_id,
        "participant_id": participant.participant_id,
        "case_id": "case-1",
        "case_name": "Case One",
        "case_version": "1",
        "score": 40,
        "max_score": 50,
    }
    fake.fail_after_result_commit = True

    with pytest.raises(database.DatabaseOperationError) as error:
        fake.save_case_result(**kwargs)
    assert error.value.retryable is True
    retried = fake.save_case_result(**kwargs)

    assert len(fake.results_by_id) == 1
    assert retried.result_id == result_id
    assert (retried.attempt_number, retried.version_attempt_number) == (1, 1)


def test_fake_store_rejects_same_result_id_with_changed_case_version():
    fake = FakeDatabase()
    participant = fake.seed_participant()
    result_id = uuid4()
    kwargs = {
        "client": fake.client,
        "result_id": result_id,
        "participant_id": participant.participant_id,
        "case_id": "case-1",
        "case_name": "Case One",
        "case_version": "1",
        "score": 40,
        "max_score": 50,
    }
    fake.save_case_result(**kwargs)

    with pytest.raises(database.DatabaseOperationError, match="idempotency"):
        fake.save_case_result(**{**kwargs, "case_version": "2"})


def test_fake_store_case_name_change_is_an_idempotent_retry():
    fake = FakeDatabase()
    participant = fake.seed_participant()
    result_id = uuid4()
    kwargs = {
        "client": fake.client,
        "result_id": result_id,
        "participant_id": participant.participant_id,
        "case_id": "case-1",
        "case_name": "Original Case Name",
        "case_version": "1",
        "score": 40,
        "max_score": 50,
    }
    original = fake.save_case_result(**kwargs)

    retried = fake.save_case_result(
        **{**kwargs, "case_name": "Editorially Renamed Case"}
    )

    assert retried == original
    assert len(fake.results_by_id) == 1
    assert (retried.attempt_number, retried.version_attempt_number) == (1, 1)


def test_case_library_has_explicit_stable_versions():
    versions = [(case.case_id, case.case_version) for case in CASES]

    assert len(versions) == len(CASES)
    assert all(
        isinstance(version, str)
        and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,39}", version)
        for _, version in versions
    )


def test_training_levels_are_one_shared_ui_database_contract():
    assert tuple(database.TRAINING_LEVELS) == tuple(LEARNER_LEVELS)


def test_migration_enforces_simplified_registration_and_version_contract():
    migration = Path(
        "supabase/migrations/20260831000000_create_vascucase_registration.sql"
    ).read_text(encoding="utf-8")
    compact = " ".join(migration.lower().split())

    assert "create table public.vascucase_participants" in compact
    assert "participant_id uuid primary key" in compact
    assert "email text not null unique" in compact
    assert "auth_user_id" not in compact
    assert "auth.users" not in compact
    assert "institution text not null" in compact
    assert "institution_number text" in compact
    assert "consent_version text not null" in compact
    assert "check (consent_version = 'vascucase-data-use-v1')" in compact
    assert "consented_at timestamptz not null default now()" in compact
    assert "case_version text not null" in compact
    assert "version_attempt_number integer not null" in compact
    assert "unique (institution_number)" not in compact
    assert "on conflict (email) do nothing" in compact
    assert "set name = excluded.name" not in compact
    assert "v_existing.case_name is distinct from" not in compact
    assert "p_email text" in compact
    assert "p_participant_id uuid" in compact
    assert "unique ( participant_id, case_id, case_version, version_attempt_number )" in compact

    migration_levels = set(
        re.findall(
            r"'(medical student|surgical resident|vascular trainee)'",
            migration,
            flags=re.IGNORECASE,
        )
    )
    assert {item.lower() for item in database.TRAINING_LEVELS} <= {
        item.lower() for item in migration_levels
    }
