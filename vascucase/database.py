from __future__ import annotations

import base64
import binascii
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

from email_validator import EmailNotValidError, validate_email
from httpx import TransportError
from postgrest.exceptions import APIError
from supabase import ClientOptions, create_client


TRAINING_LEVELS = (
    "Medical student",
    "Surgical resident",
    "Vascular trainee",
)
CONSENT_VERSION = "vascucase-data-use-v1"


class DatabaseError(RuntimeError):
    """Base class for safe, user-facing database failures."""


class DatabaseConfigurationError(DatabaseError):
    """Raised when Supabase server credentials are absent or malformed."""


class DatabaseOperationError(DatabaseError):
    """Raised when a Supabase operation cannot be completed safely."""

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class DatabaseResponseValidationError(DatabaseOperationError):
    """Raised when a successful RPC returns an unsupported or ambiguous shape."""

    def __init__(self, description: str, response_shape: str) -> None:
        self.description = description
        self.response_shape = response_shape
        super().__init__(
            "Supabase returned an invalid "
            f"{description} response shape ({response_shape})."
        )


@dataclass(frozen=True)
class ParticipantRecord:
    participant_id: UUID
    name: str
    email: str
    training_level: str
    institution: str
    institution_number: str | None
    consent_given: bool
    consent_version: str
    consented_at: datetime
    registered_at: datetime


@dataclass(frozen=True)
class CaseResultRecord:
    result_id: UUID
    participant_id: UUID
    case_id: str
    case_version: str
    case_name: str
    score: int
    max_score: int
    percentage: Decimal
    attempt_number: int
    version_attempt_number: int
    completed_at: datetime


ClientFactory = Callable[[str, str], Any]


def normalize_name(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Enter a full name between 2 and 120 characters.")
    normalized = " ".join(value.split())
    if not 2 <= len(normalized) <= 120:
        raise ValueError("Enter a full name between 2 and 120 characters.")
    return normalized


def normalize_email(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Enter a valid email address.")
    candidate = value.strip()
    try:
        normalized = validate_email(candidate, check_deliverability=False).normalized
    except EmailNotValidError as exc:
        raise ValueError("Enter a valid email address.") from exc
    return normalized.lower()


def normalize_training_level(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Select your current training level.")
    normalized = " ".join(value.split())
    if normalized not in TRAINING_LEVELS:
        raise ValueError("Select your current training level.")
    return normalized


def normalize_institution(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Enter your institution.")
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError("Enter your institution.")
    return normalized


def normalize_institution_number(
    value: str | None,
    *,
    training_level: str,
) -> str | None:
    normalized_level = normalize_training_level(training_level)
    if value is None:
        normalized = None
    elif isinstance(value, str):
        normalized = value.strip() or None
    else:
        raise ValueError("Enter a valid institution number.")
    if normalized_level == "Medical student" and normalized is None:
        raise ValueError("Institution number is required for medical students.")
    return normalized


def normalize_case_version(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Case version is required.")
    return value.strip()


def _legacy_key_has_service_role(key: str) -> bool:
    parts = key.split(".")
    if len(parts) != 3:
        return False
    try:
        payload = parts[1] + "=" * (-len(parts[1]) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload).decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError, binascii.Error):
        return False
    return isinstance(claims, dict) and claims.get("role") == "service_role"


def validate_supabase_url(value: str) -> str:
    if not isinstance(value, str):
        raise DatabaseConfigurationError("Supabase access is not configured correctly.")
    url = value.strip().rstrip("/")
    parsed = urlparse(url)
    hostname = parsed.hostname
    is_secure_remote = parsed.scheme == "https" and bool(hostname)
    is_local = parsed.scheme == "http" and hostname in {"localhost", "127.0.0.1", "::1"}
    if (
        not (is_secure_remote or is_local)
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise DatabaseConfigurationError("Supabase access is not configured with a valid project URL.")
    return url


def validate_supabase_secret_key(value: str) -> str:
    if not isinstance(value, str):
        raise DatabaseConfigurationError("Supabase access is not configured correctly.")
    key = value.strip()
    placeholder = key.upper()
    if (
        not key
        or any(marker in placeholder for marker in ("YOUR_", "PLACEHOLDER", "REPLACE_ME"))
        or any(character.isspace() for character in key)
    ):
        raise DatabaseConfigurationError("Supabase access is not configured with a server secret key.")
    if key.startswith("sb_publishable_") or not (
        key.startswith("sb_secret_") or _legacy_key_has_service_role(key)
    ):
        raise DatabaseConfigurationError("Supabase access requires a server secret key.")
    return key


def supabase_credentials_from_secrets(secrets: Mapping[str, Any]) -> tuple[str, str]:
    try:
        url = secrets["SUPABASE_URL"]
        key = secrets["SUPABASE_SECRET_KEY"]
    except (KeyError, TypeError, FileNotFoundError) as exc:
        raise DatabaseConfigurationError(
            "Supabase access is not configured. Add SUPABASE_URL and "
            "SUPABASE_SECRET_KEY to Streamlit secrets."
        ) from exc
    return validate_supabase_url(url), validate_supabase_secret_key(key)


def supabase_service_client_from_secrets(
    secrets: Mapping[str, Any],
    *,
    client_factory: ClientFactory | None = None,
) -> Any:
    url, key = supabase_credentials_from_secrets(secrets)
    try:
        if client_factory is not None:
            return client_factory(url, key)
        return create_client(
            url,
            key,
            options=ClientOptions(
                auto_refresh_token=False,
                persist_session=False,
            ),
        )
    except Exception as exc:
        raise DatabaseConfigurationError("The Supabase client could not be initialized.") from exc


def supabase_client_from_secrets(
    secrets: Mapping[str, Any],
    *,
    client_factory: ClientFactory | None = None,
) -> Any:
    """Compatibility name for the server-only service-role client factory."""

    return supabase_service_client_from_secrets(
        secrets,
        client_factory=client_factory,
    )


def _uuid(value: UUID | str, field_name: str) -> UUID:
    try:
        return value if isinstance(value, UUID) else UUID(str(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"{field_name} must be a valid UUID.") from exc


def _datetime(value: datetime | str, field_name: str) -> datetime:
    try:
        parsed = (
            value
            if isinstance(value, datetime)
            else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        )
    except (TypeError, ValueError) as exc:
        raise DatabaseOperationError(f"Supabase returned an invalid {field_name}.") from exc
    if parsed.tzinfo is None:
        raise DatabaseOperationError(f"Supabase returned an invalid {field_name}.")
    return parsed.astimezone(timezone.utc)


def _single_row(data: Any, description: str) -> Mapping[str, Any]:
    """Normalize the two one-row shapes returned by supported postgrest versions."""

    if isinstance(data, Mapping):
        return dict(data)
    if (
        isinstance(data, list)
        and len(data) == 1
        and isinstance(data[0], Mapping)
    ):
        return dict(data[0])
    response_shape = (
        f"list[{len(data)}]" if isinstance(data, list) else type(data).__name__
    )
    raise DatabaseResponseValidationError(description, response_shape)


def _execute_rpc(
    client: Any,
    function_name: str,
    params: Mapping[str, Any],
    *,
    failure_message: str,
    permanent_failure_message: str,
    description: str,
) -> Mapping[str, Any]:
    try:
        response = client.rpc(function_name, dict(params)).execute()
    except Exception as exc:
        retryable = _is_retryable_supabase_error(exc)
        message = failure_message if retryable else permanent_failure_message
        raise DatabaseOperationError(message, retryable=retryable) from exc
    return _single_row(getattr(response, "data", None), description)


def _is_retryable_supabase_error(error: Exception) -> bool:
    if isinstance(error, TransportError):
        return True
    if not isinstance(error, APIError):
        return False
    code = str(getattr(error, "code", ""))
    return code.startswith(("08", "40", "53", "57")) or code in {
        "55P03",
        "PGRST000",
        "PGRST001",
        "PGRST002",
    }


def _participant_from_row(row: Mapping[str, Any]) -> ParticipantRecord:
    try:
        if row["consent_given"] is not True:
            raise TypeError("consent_given must be true")
        name = normalize_name(row["name"])
        email = normalize_email(row["email"])
        training_level = normalize_training_level(row["training_level"])
        institution = normalize_institution(row["institution"])
        institution_number = normalize_institution_number(
            row["institution_number"],
            training_level=training_level,
        )
        if (
            row["name"] != name
            or row["email"] != email
            or row["training_level"] != training_level
            or row["institution"] != institution
            or row["institution_number"] != institution_number
            or row["consent_version"] != CONSENT_VERSION
        ):
            raise TypeError("participant fields must be normalized")
        return ParticipantRecord(
            participant_id=_uuid(row["participant_id"], "participant_id"),
            name=name,
            email=email,
            training_level=training_level,
            institution=institution,
            institution_number=institution_number,
            consent_given=True,
            consent_version=CONSENT_VERSION,
            consented_at=_datetime(row["consented_at"], "consented_at"),
            registered_at=_datetime(row["registered_at"], "registered_at"),
        )
    except DatabaseError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise DatabaseOperationError(
            "Supabase returned an incomplete participant registration."
        ) from exc


def _result_from_row(row: Mapping[str, Any]) -> CaseResultRecord:
    try:
        version_attempt_number = row["version_attempt_number"]
        integer_values = (
            row["score"],
            row["max_score"],
            row["attempt_number"],
            version_attempt_number,
        )
        if any(type(value) is not int for value in integer_values):
            raise TypeError("numeric result fields must be integers")
        percentage = Decimal(str(row["percentage"])).quantize(Decimal("0.01"))
        if not percentage.is_finite():
            raise ValueError("percentage must be finite")
        participant_id = row["participant_id"]
        case_version = normalize_case_version(row["case_version"])
        return CaseResultRecord(
            result_id=_uuid(row["result_id"], "result_id"),
            participant_id=_uuid(participant_id, "participant_id"),
            case_id=str(row["case_id"]),
            case_version=case_version,
            case_name=str(row["case_name"]),
            score=row["score"],
            max_score=row["max_score"],
            percentage=percentage,
            attempt_number=row["attempt_number"],
            version_attempt_number=version_attempt_number,
            completed_at=_datetime(row["completed_at"], "completed_at"),
        )
    except DatabaseError:
        raise
    except (KeyError, TypeError, ValueError, ArithmeticError) as exc:
        raise DatabaseOperationError("Supabase returned an incomplete case result.") from exc


def register_participant(
    *,
    client: Any,
    name: str,
    email: str,
    training_level: str,
    institution: str,
    institution_number: str | None,
    consent_given: bool,
    consent_version: str = CONSENT_VERSION,
) -> ParticipantRecord:
    normalized_name = normalize_name(name)
    normalized_email = normalize_email(email)
    normalized_level = normalize_training_level(training_level)
    normalized_institution = normalize_institution(institution)
    normalized_number = normalize_institution_number(
        institution_number,
        training_level=normalized_level,
    )
    if consent_given is not True:
        raise ValueError("Privacy and data-use consent is required.")
    if consent_version != CONSENT_VERSION:
        raise ValueError("The current privacy and data-use notice is required.")

    row = _execute_rpc(
        client,
        "register_vascucase_participant",
        {
            "p_name": normalized_name,
            "p_email": normalized_email,
            "p_training_level": normalized_level,
            "p_institution": normalized_institution,
            "p_institution_number": normalized_number,
            "p_consent_given": True,
            "p_consent_version": CONSENT_VERSION,
        },
        failure_message=(
            "Registration could not be saved because Supabase is temporarily unavailable."
        ),
        permanent_failure_message=(
            "Registration could not be saved because Supabase rejected the request."
        ),
        description="participant registration",
    )
    participant = _participant_from_row(row)
    if (
        participant.name != normalized_name
        or participant.email != normalized_email
        or participant.training_level != normalized_level
        or participant.institution != normalized_institution
        or participant.institution_number != normalized_number
        or participant.consent_given is not True
        or participant.consent_version != CONSENT_VERSION
    ):
        raise DatabaseOperationError(
            "Supabase returned a mismatched participant registration."
        )
    return participant


def save_case_result(
    *,
    client: Any,
    result_id: UUID | str,
    participant_id: UUID | str,
    case_id: str,
    case_version: str,
    case_name: str,
    score: int,
    max_score: int,
) -> CaseResultRecord:
    result_uuid = _uuid(result_id, "result_id")
    participant_uuid = _uuid(participant_id, "participant_id")
    if not isinstance(case_id, str) or not isinstance(case_name, str):
        raise ValueError("Case identity is required.")
    normalized_case_id = case_id.strip()
    normalized_case_version = normalize_case_version(case_version)
    normalized_case_name = " ".join(case_name.split())
    if not normalized_case_id or not normalized_case_name:
        raise ValueError("Case identity is required.")
    if isinstance(score, bool) or isinstance(max_score, bool):
        raise ValueError("Scores must be integers.")
    if not isinstance(score, int) or not isinstance(max_score, int):
        raise ValueError("Scores must be integers.")
    if max_score <= 0 or score < 0 or score > max_score:
        raise ValueError("Score must be between zero and max_score.")

    params = {
        "p_participant_id": str(participant_uuid),
        "p_case_id": normalized_case_id,
        "p_case_version": normalized_case_version,
        "p_case_name": normalized_case_name,
        "p_score": score,
        "p_max_score": max_score,
        "p_result_id": str(result_uuid),
    }

    row = _execute_rpc(
        client,
        "save_vascucase_result",
        params,
        failure_message=(
            "The case result could not be saved because Supabase is temporarily unavailable."
        ),
        permanent_failure_message=(
            "The case result could not be saved because Supabase rejected the request."
        ),
        description="case result",
    )
    stored = _result_from_row(row)
    expected_percentage = (
        Decimal(score) * Decimal(100) / Decimal(max_score)
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if (
        stored.result_id != result_uuid
        or stored.participant_id != participant_uuid
        or stored.case_id != normalized_case_id
        or stored.case_version != normalized_case_version
        or stored.score != score
        or stored.max_score != max_score
        or stored.percentage != expected_percentage
        or stored.attempt_number < 1
        or stored.version_attempt_number < 1
    ):
        raise DatabaseOperationError("Supabase returned a mismatched case result.")
    return stored
