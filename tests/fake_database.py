from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID, uuid4

from vascucase import database


@dataclass(frozen=True)
class FakeParticipantRecord:
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
class FakeCaseResultRecord:
    result_id: UUID
    participant_id: UUID
    case_id: str
    case_name: str
    case_version: str
    score: int
    max_score: int
    percentage: Decimal
    attempt_number: int
    version_attempt_number: int
    completed_at: datetime


class FakeDatabase:
    """In-memory registration/result boundary used by Streamlit flow tests."""

    def __init__(self) -> None:
        self.client = object()
        self.participants_by_email: dict[str, FakeParticipantRecord] = {}
        self.results_by_id: dict[UUID, FakeCaseResultRecord] = {}
        self.registration_calls: list[dict[str, object]] = []
        self.result_calls: list[dict[str, object]] = []
        self.fail_next_registration = False
        self.fail_after_registration_commit = False
        self.fail_next_result_save = False
        self.fail_after_result_commit = False

    def install(self, monkeypatch) -> None:
        monkeypatch.setattr(
            database,
            "supabase_client_from_secrets",
            lambda _secrets: self.client,
        )
        monkeypatch.setattr(database, "register_participant", self.register_participant)
        monkeypatch.setattr(database, "save_case_result", self.save_case_result)

    def seed_participant(
        self,
        *,
        email: str = "alex@example.com",
        name: str = "Alex Morgan",
        training_level: str = "Surgical resident",
        institution: str = "Yarmouk University",
        institution_number: str | None = None,
    ) -> FakeParticipantRecord:
        normalized_email = database.normalize_email(email)
        now = datetime.now(timezone.utc)
        record = FakeParticipantRecord(
            participant_id=uuid4(),
            name=database.normalize_name(name),
            email=normalized_email,
            training_level=database.normalize_training_level(training_level),
            institution=database.normalize_institution(institution),
            institution_number=database.normalize_institution_number(
                institution_number,
                training_level=training_level,
            ),
            consent_given=True,
            consent_version=database.CONSENT_VERSION,
            consented_at=now,
            registered_at=now,
        )
        self.participants_by_email[normalized_email] = record
        return record

    def register_participant(
        self,
        *,
        client: object,
        name: str,
        email: str,
        training_level: str,
        institution: str,
        institution_number: str | None,
        consent_given: bool,
        consent_version: str = database.CONSENT_VERSION,
    ) -> FakeParticipantRecord:
        assert client is self.client
        normalized_name = database.normalize_name(name)
        normalized_email = database.normalize_email(email)
        normalized_level = database.normalize_training_level(training_level)
        normalized_institution = database.normalize_institution(institution)
        normalized_number = database.normalize_institution_number(
            institution_number,
            training_level=normalized_level,
        )
        if consent_given is not True or consent_version != database.CONSENT_VERSION:
            raise ValueError("Privacy and data-use consent is required.")

        submitted = {
            "name": normalized_name,
            "email": normalized_email,
            "training_level": normalized_level,
            "institution": normalized_institution,
            "institution_number": normalized_number,
            "consent_given": True,
            "consent_version": database.CONSENT_VERSION,
        }
        self.registration_calls.append(submitted)
        if self.fail_next_registration:
            self.fail_next_registration = False
            raise database.DatabaseOperationError(
                "Registration could not be completed.", retryable=True
            )

        existing = self.participants_by_email.get(normalized_email)
        if existing is not None:
            existing_demographics = (
                existing.name,
                existing.training_level,
                existing.institution,
                existing.institution_number,
                existing.consent_given,
                existing.consent_version,
            )
            submitted_demographics = (
                normalized_name,
                normalized_level,
                normalized_institution,
                normalized_number,
                True,
                database.CONSENT_VERSION,
            )
            if existing_demographics != submitted_demographics:
                raise database.DatabaseOperationError(
                    "Registration could not be completed.", retryable=False
                )
            return existing

        now = datetime.now(timezone.utc)
        record = FakeParticipantRecord(
            participant_id=uuid4(),
            name=normalized_name,
            email=normalized_email,
            training_level=normalized_level,
            institution=normalized_institution,
            institution_number=normalized_number,
            consent_given=True,
            consent_version=database.CONSENT_VERSION,
            consented_at=now,
            registered_at=now,
        )
        self.participants_by_email[normalized_email] = record
        if self.fail_after_registration_commit:
            self.fail_after_registration_commit = False
            raise database.DatabaseOperationError(
                "Registration could not be completed.", retryable=True
            )
        return record

    def save_case_result(
        self,
        *,
        client: object,
        result_id: UUID | str,
        participant_id: UUID | str,
        case_id: str,
        case_name: str,
        case_version: str,
        score: int,
        max_score: int,
    ) -> FakeCaseResultRecord:
        assert client is self.client
        result_uuid = UUID(str(result_id))
        participant_uuid = UUID(str(participant_id))
        payload = {
            "result_id": result_uuid,
            "participant_id": participant_uuid,
            "case_id": case_id,
            "case_name": case_name,
            "case_version": case_version,
            "score": score,
            "max_score": max_score,
        }
        self.result_calls.append(payload)
        if self.fail_next_result_save:
            self.fail_next_result_save = False
            raise database.DatabaseOperationError(
                "temporary test failure", retryable=True
            )

        existing = self.results_by_id.get(result_uuid)
        if existing is not None:
            immutable = (
                existing.participant_id,
                existing.case_id,
                existing.case_version,
                existing.score,
                existing.max_score,
            )
            submitted = (
                participant_uuid,
                case_id,
                case_version,
                score,
                max_score,
            )
            if immutable != submitted:
                raise database.DatabaseOperationError("idempotency conflict")
            return existing

        if not any(
            item.participant_id == participant_uuid
            for item in self.participants_by_email.values()
        ):
            raise database.DatabaseOperationError("unknown participant")
        prior = [
            item
            for item in self.results_by_id.values()
            if item.participant_id == participant_uuid and item.case_id == case_id
        ]
        prior_version = [
            item for item in prior if item.case_version == case_version
        ]
        percentage = (
            Decimal(score) * Decimal(100) / Decimal(max_score)
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        record = FakeCaseResultRecord(
            result_id=result_uuid,
            participant_id=participant_uuid,
            case_id=case_id,
            case_name=case_name,
            case_version=case_version,
            score=score,
            max_score=max_score,
            percentage=percentage,
            attempt_number=max(
                (item.attempt_number for item in prior), default=0
            )
            + 1,
            version_attempt_number=max(
                (item.version_attempt_number for item in prior_version),
                default=0,
            )
            + 1,
            completed_at=datetime.now(timezone.utc),
        )
        self.results_by_id[result_uuid] = record
        if self.fail_after_result_commit:
            self.fail_after_result_commit = False
            raise database.DatabaseOperationError(
                "ambiguous test failure", retryable=True
            )
        return record
