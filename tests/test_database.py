from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from httpx import TimeoutException
from postgrest.exceptions import APIError

from vascucase import database


VALID_URL = "https://project-ref.supabase.co"
VALID_SECRET = "sb_secret_test"


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
    training_level="Surgical resident",
    institution="Yarmouk University",
    institution_number=None,
    consent_version=None,
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
        "consent_version": consent_version or database.CONSENT_VERSION,
        "consented_at": consented_at,
        "registered_at": registered_at,
    }


def _result_row(
    *,
    result_id,
    participant_id=None,
    case_id="case-1",
    case_name="Case One",
    case_version="1",
    score=37,
    max_score=50,
    percentage="74.00",
    attempt_number=2,
    version_attempt_number=1,
    completed_at="2026-08-31T10:30:00+00:00",
):
    return {
        "result_id": str(result_id),
        "participant_id": str(participant_id or uuid4()),
        "case_id": case_id,
        "case_name": case_name,
        "case_version": case_version,
        "score": score,
        "max_score": max_score,
        "percentage": percentage,
        "attempt_number": attempt_number,
        "version_attempt_number": version_attempt_number,
        "completed_at": completed_at,
    }


def _registration_kwargs(client):
    return {
        "client": client,
        "name": "Alex Morgan",
        "email": "alex@example.com",
        "training_level": "Surgical resident",
        "institution": "Yarmouk University",
        "institution_number": None,
        "consent_given": True,
        "consent_version": database.CONSENT_VERSION,
    }


def _result_kwargs(client, *, result_id=None, participant_id=None):
    return {
        "client": client,
        "result_id": result_id or uuid4(),
        "participant_id": participant_id or uuid4(),
        "case_id": "case-1",
        "case_name": "Case One",
        "case_version": "1",
        "score": 37,
        "max_score": 50,
    }


def test_email_is_validated_trimmed_and_lowercased():
    assert database.normalize_email("  Learner+Case@Example.COM  ") == (
        "learner+case@example.com"
    )


@pytest.mark.parametrize(
    "value",
    ["", "not-an-email", "missing@", "@example.com", "two@@example.com", "a b@example.com"],
)
def test_invalid_email_is_rejected(value):
    with pytest.raises(ValueError, match="valid email"):
        database.normalize_email(value)


def test_supabase_client_uses_exact_streamlit_secret_names():
    captured = {}
    sentinel = object()

    def factory(url, key):
        captured["url"] = url
        captured["key"] = key
        return sentinel

    client = database.supabase_client_from_secrets(
        {
            "SUPABASE_URL": f"  {VALID_URL}/  ",
            "SUPABASE_SECRET_KEY": VALID_SECRET,
        },
        client_factory=factory,
    )

    assert client is sentinel
    assert captured == {"url": VALID_URL, "key": VALID_SECRET}


@pytest.mark.parametrize(
    "secrets",
    [
        {},
        {"SUPABASE_URL": VALID_URL},
        {"SUPABASE_SECRET_KEY": VALID_SECRET},
        {"SUPABASE_URL": VALID_URL, "SUPABASE_SECRET_KEY": ""},
        {"SUPABASE_URL": "http://example.com", "SUPABASE_SECRET_KEY": VALID_SECRET},
        {
            "SUPABASE_URL": f"{VALID_URL}/rest/v1",
            "SUPABASE_SECRET_KEY": VALID_SECRET,
        },
        {
            "SUPABASE_URL": VALID_URL,
            "SUPABASE_SECRET_KEY": "sb_publishable_not_a_server_secret",
        },
        {"database": {"url": "postgresql://ignored.example/db"}},
    ],
)
def test_invalid_supabase_configuration_is_sanitized(secrets):
    with pytest.raises(database.DatabaseConfigurationError) as error:
        database.supabase_client_from_secrets(
            secrets,
            client_factory=lambda _url, _key: pytest.fail(
                "client should not be created"
            ),
        )

    assert VALID_SECRET not in str(error.value)
    assert "postgresql://" not in str(error.value)


def test_registration_supabase_failure_is_sanitized_and_retryable():
    client = RecordingSupabaseClient([TimeoutException("private backend detail")])

    with pytest.raises(database.DatabaseOperationError) as error:
        database.register_participant(**_registration_kwargs(client))

    assert "temporarily unavailable" in str(error.value)
    assert "private backend" not in str(error.value)
    assert error.value.retryable is True


def test_material_duplicate_conflict_is_neutral_and_not_retryable():
    client = RecordingSupabaseClient(
        [APIError({"message": "participant email already exists", "code": "23505"})]
    )

    with pytest.raises(database.DatabaseOperationError) as error:
        database.register_participant(**_registration_kwargs(client))

    message = str(error.value).lower()
    assert error.value.retryable is False
    assert "participant email already exists" not in message
    assert "alex@example.com" not in message
    assert all(word not in message for word in ("existing", "conflict", "mismatch"))


def test_registration_accepts_dictionary_rpc_response_data():
    row = _participant_row()
    client = RecordingSupabaseClient([row])

    participant = database.register_participant(**_registration_kwargs(client))

    assert str(participant.participant_id) == row["participant_id"]
    assert participant.email == row["email"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("participant_id", "not-a-uuid"),
        ("name", "Different Name"),
        ("email", "different@example.com"),
        ("training_level", "Vascular trainee"),
        ("institution", "Different Institution"),
        ("institution_number", "123"),
        ("consent_given", False),
        ("consent_version", "obsolete"),
        ("consented_at", "2026-08-31T09:00:00"),
        ("registered_at", "2026-08-31T09:00:00"),
    ],
)
def test_malformed_or_mismatched_registration_response_fails_closed(field, value):
    row = _participant_row()
    row[field] = value
    client = RecordingSupabaseClient([[row]])

    with pytest.raises(database.DatabaseOperationError):
        database.register_participant(**_registration_kwargs(client))


@pytest.mark.parametrize(
    ("response_data", "expected_shape"),
    [([], "list[0]"), ([{}, {}], "list[2]"), (None, "NoneType")],
)
def test_registration_requires_exactly_one_complete_response_row(
    response_data,
    expected_shape,
):
    client = RecordingSupabaseClient([response_data])

    with pytest.raises(database.DatabaseResponseValidationError) as error:
        database.register_participant(**_registration_kwargs(client))

    assert error.value.retryable is False
    assert error.value.response_shape == expected_shape


def test_result_supabase_failure_is_sanitized_and_retryable():
    client = RecordingSupabaseClient([TimeoutException("private backend detail")])

    with pytest.raises(database.DatabaseOperationError) as error:
        database.save_case_result(**_result_kwargs(client))

    assert "temporarily unavailable" in str(error.value)
    assert "private backend" not in str(error.value)
    assert error.value.retryable is True


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("result_id", "not-a-uuid"),
        ("participant_id", str(uuid4())),
        ("case_id", "different-case"),
        ("case_version", "2"),
        ("score", 36),
        ("score", True),
        ("max_score", 51),
        ("percentage", "75.00"),
        ("attempt_number", 0),
        ("attempt_number", True),
        ("version_attempt_number", 0),
        ("version_attempt_number", True),
        ("completed_at", "not-a-timestamp"),
    ],
)
def test_malformed_or_mismatched_result_response_fails_closed(field, value):
    participant_id = uuid4()
    result_id = uuid4()
    row = _result_row(result_id=result_id, participant_id=participant_id)
    row[field] = value
    client = RecordingSupabaseClient([[row]])

    with pytest.raises(database.DatabaseOperationError):
        database.save_case_result(
            **_result_kwargs(
                client,
                result_id=result_id,
                participant_id=participant_id,
            )
        )


def test_result_maps_database_generated_fields_and_both_attempts():
    participant_id = uuid4()
    result_id = uuid4()
    client = RecordingSupabaseClient(
        [[_result_row(result_id=result_id, participant_id=participant_id)]]
    )

    stored = database.save_case_result(
        **_result_kwargs(
            client,
            result_id=result_id,
            participant_id=participant_id,
        )
    )

    assert stored.percentage == Decimal("74.00")
    assert (stored.attempt_number, stored.version_attempt_number) == (2, 1)
    assert stored.completed_at == datetime(
        2026, 8, 31, 10, 30, tzinfo=timezone.utc
    )
    assert "p_completed_at" not in client.calls[0][1]


def test_result_accepts_dictionary_rpc_response_data():
    participant_id = uuid4()
    result_id = uuid4()
    row = _result_row(result_id=result_id, participant_id=participant_id)
    client = RecordingSupabaseClient([row])

    stored = database.save_case_result(
        **_result_kwargs(
            client,
            result_id=result_id,
            participant_id=participant_id,
        )
    )

    assert stored.result_id == result_id
    assert stored.participant_id == participant_id


def test_result_invalid_rpc_response_shape_is_classified_nonretryable():
    client = RecordingSupabaseClient([[{}, {}]])

    with pytest.raises(database.DatabaseResponseValidationError) as error:
        database.save_case_result(**_result_kwargs(client))

    assert error.value.retryable is False
    assert error.value.description == "case result"
    assert error.value.response_shape == "list[2]"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("score", -1),
        ("score", 101),
        ("score", True),
        ("max_score", 0),
        ("max_score", False),
        ("case_version", ""),
        ("case_version", "   "),
    ],
)
def test_invalid_result_payload_is_rejected_before_supabase_access(field, value):
    client = RecordingSupabaseClient([])
    kwargs = _result_kwargs(client)
    kwargs[field] = value

    with pytest.raises(ValueError):
        database.save_case_result(**kwargs)

    assert client.calls == []


def test_repository_uses_supabase_dependency_and_placeholder_secrets():
    requirements = Path("requirements.txt").read_text(encoding="utf-8")
    example = Path(".streamlit/secrets.toml.example").read_text(encoding="utf-8")

    assert "supabase==" in requirements
    assert "psycopg" not in requirements
    assert 'SUPABASE_URL = "https://YOUR_PROJECT_REF.supabase.co"' in example
    assert 'SUPABASE_SECRET_KEY = "YOUR_SUPABASE_SECRET_KEY"' in example
    assert "SUPABASE_PUBLISHABLE_KEY" not in example
    assert "SUPABASE_ANON_KEY" not in example
    assert "postgresql://" not in example
