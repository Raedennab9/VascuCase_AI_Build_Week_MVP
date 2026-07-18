from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


QuestionKind = Literal["single", "multi"]
Difficulty = Literal["Intermediate", "Advanced"]


class AnswerOption(BaseModel):
    model_config = ConfigDict(frozen=True)

    option_id: str = Field(pattern=r"^[a-z0-9_]+$")
    label: str = Field(min_length=3)


class Question(BaseModel):
    model_config = ConfigDict(frozen=True)

    question_id: str = Field(pattern=r"^[a-z0-9_]+$")
    prompt: str = Field(min_length=10)
    kind: QuestionKind
    options: tuple[AnswerOption, ...] = Field(min_length=2)
    min_selections: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def validate_question(self) -> "Question":
        option_ids = [option.option_id for option in self.options]
        if len(option_ids) != len(set(option_ids)):
            raise ValueError(f"Duplicate option ID in question {self.question_id}")
        if self.kind == "single" and self.min_selections != 1:
            raise ValueError("Single-choice questions must require exactly one answer")
        if self.min_selections > len(self.options):
            raise ValueError("min_selections cannot exceed the number of options")
        return self


class CaseStage(BaseModel):
    model_config = ConfigDict(frozen=True)

    stage_id: str = Field(pattern=r"^stage[1-4]$")
    title: str = Field(min_length=5)
    domain: str = Field(min_length=4)
    content: str = Field(min_length=40)
    question: Question


class UnsafeChoice(BaseModel):
    model_config = ConfigDict(frozen=True)

    penalty: int = Field(ge=1, le=25)
    explanation: str = Field(min_length=10)


class Reference(BaseModel):
    model_config = ConfigDict(frozen=True)

    citation: str = Field(min_length=10)
    url: HttpUrl


class VascularCase(BaseModel):
    """Validated, identifier-free educational case and authoritative rubric."""

    model_config = ConfigDict(frozen=True)

    case_id: str = Field(pattern=r"^[a-z0-9_]+$")
    title: str = Field(min_length=5)
    category: str = Field(min_length=4)
    difficulty: Difficulty
    brief_presentation: str = Field(min_length=40)
    stages: tuple[CaseStage, ...] = Field(min_length=4, max_length=4)
    correct_actions: tuple[str, ...] = Field(min_length=4)
    critical_actions: tuple[str, ...] = Field(min_length=1)
    unsafe_choices: dict[str, UnsafeChoice] = Field(min_length=1)
    scoring_weights: dict[str, int] = Field(min_length=4)
    classification_criteria: tuple[str, ...] = Field(min_length=1)
    explanations: dict[str, str] = Field(min_length=1)
    model_pathway: tuple[str, ...] = Field(min_length=4)
    final_diagnosis: str = Field(min_length=10)
    learning_points: tuple[str, ...] = Field(min_length=2)
    references: tuple[Reference, ...] = Field(min_length=1)
    educational_disclaimer: str = Field(min_length=30)
    fictional: Literal[True] = True
    contains_real_patient_information: Literal[False] = False

    @model_validator(mode="after")
    def validate_case_and_rubric(self) -> "VascularCase":
        expected_stage_ids = [f"stage{number}" for number in range(1, 5)]
        actual_stage_ids = [stage.stage_id for stage in self.stages]
        if actual_stage_ids != expected_stage_ids:
            raise ValueError("Cases must contain stage1 through stage4 in order")

        option_ids = [
            option.option_id
            for stage in self.stages
            for option in stage.question.options
        ]
        if len(option_ids) != len(set(option_ids)):
            raise ValueError("Option IDs must be unique within a case")
        known_options = set(option_ids)

        correct = set(self.correct_actions)
        if correct != set(self.scoring_weights):
            raise ValueError("Correct actions must exactly match scoring weight IDs")
        if not correct <= known_options:
            raise ValueError("Every correct action ID must exist in the case options")
        if not set(self.critical_actions) <= correct:
            raise ValueError("Critical actions must be scored correct actions")

        unsafe = set(self.unsafe_choices)
        if not unsafe <= known_options:
            raise ValueError("Every unsafe choice ID must exist in the case options")
        if unsafe & correct:
            raise ValueError("A choice cannot be both correct and unsafe")
        if sum(self.scoring_weights.values()) != 100:
            raise ValueError("Every case rubric must total exactly 100 points")
        if any(weight <= 0 for weight in self.scoring_weights.values()):
            raise ValueError("Scoring weights must be positive")

        explained = set(self.explanations)
        if not (correct | unsafe) <= explained:
            raise ValueError("Every correct and unsafe choice needs an explanation")

        question_ids = [stage.question.question_id for stage in self.stages]
        if len(question_ids) != len(set(question_ids)):
            raise ValueError("Question IDs must be unique within a case")

        # The library is synthetic and deliberately contains no patient identifiers.
        # Reject common identifier fields if one is accidentally introduced later.
        clinical_text = " ".join(
            [self.title, self.brief_presentation, self.final_diagnosis]
            + [stage.content for stage in self.stages]
        )
        prohibited = re.compile(
            r"\b(?:MRN|medical record number|NHS number|date of birth|DOB\s*:|passport number|national ID)\b",
            re.IGNORECASE,
        )
        if prohibited.search(clinical_text):
            raise ValueError("Cases must not contain real-patient identifier fields")
        return self

    @property
    def option_labels(self) -> dict[str, str]:
        return {
            option.option_id: option.label
            for stage in self.stages
            for option in stage.question.options
        }

    @property
    def option_domains(self) -> dict[str, str]:
        return {
            option.option_id: stage.domain
            for stage in self.stages
            for option in stage.question.options
        }

    @property
    def domain_max_scores(self) -> dict[str, int]:
        domains = self.option_domains
        totals: dict[str, int] = {}
        for option_id, weight in self.scoring_weights.items():
            domain = domains[option_id]
            totals[domain] = totals.get(domain, 0) + weight
        return totals
