import json
import os
from unittest.mock import patch
from uuid import uuid4

import pytest
import sqlalchemy.dialects.postgresql as pg_dialect
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import JSON
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from ..src.controllers import task_generation as _task_gen_module
from ..src.controllers.task_generation import router
from ..src.database.dao_connection import get_session
from ..src.models.Enums.License import License
from ..src.models.Enums.Questiontypes import QuestionTypes
from ..src.models.Enums.Status import Status
from ..src.models.Enums.Themenbereich import Themenbereich
from ..src.models.author import Creator
from ..src.models.organisation import Organisation
from ..src.schemas.Tasks.Item import (
    ItemCreate,
    MultipleChoiceOption,
    MultipleChoiceQuestionPayload,
    MultipleChoiceSolutionPayload,
)

os.environ.setdefault("PG_USER", "test")
os.environ.setdefault("PG_PW", "test")
os.environ.setdefault("PG_DB", "test")
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")

pg_dialect.JSONB = JSON  # SQLite kennt kein JSONB – auf JSON umbiegen


# ---------------------------------------------------------------------------
# Test-DB-Setup
# ---------------------------------------------------------------------------

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    app = FastAPI()
    app.include_router(router)

    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session

    with patch.object(_task_gen_module, "run_on_item_create"):
        with TestClient(app) as c:
            yield c


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _create_organisation(session: Session) -> Organisation:
    org = Organisation(name="Test-Uni", contact="test@uni.de", faculty="Informatik")
    session.add(org)
    session.commit()
    session.refresh(org)
    return org


def _create_creator(session: Session, org_id) -> Creator:
    creator = Creator(name="Max Mustermann", email="max@test.de", role=1, organisation_id=org_id)
    session.add(creator)
    session.commit()
    session.refresh(creator)
    return creator


def _default_item_metadata() -> dict:
    return {"bloomlevel": "apply"}


def _freitext_item_payload(author_id) -> dict:
    return {
        "fragestellung": "Was ist eine Transaktion?",
        "question_type": QuestionTypes.FREITEXT.value,
        "license": License.CC_BY.value,
        "status": Status.DRAFT.value,
        "author_id": str(author_id),
        "solution": "Eine atomare Folge von DB-Operationen.",
        "item_metadata": _default_item_metadata(),
    }


def _multiple_choice_payload(author_id) -> dict:
    options = [
        {"option_id": "a", "text": "Ja"},
        {"option_id": "b", "text": "Nein"},
    ]
    return {
        "fragestellung": {
            "prompt": "Ist SQL eine Sprache?",
            "options": options,
        },
        "question_type": QuestionTypes.MULTIPLECHOICE.value,
        "license": License.CC0.value,
        "status": Status.DRAFT.value,
        "author_id": str(author_id),
        "solution": {
            "options": options,
            "correct_option_ids": ["a"],
        },
        "item_metadata": _default_item_metadata(),
    }


# ===========================================================================
# Schema-Validierung: ItemCreate
# ===========================================================================

def freitext_item_create_accepts_plain_string():
    payload = ItemCreate(
        fragestellung="Erkläre den ACID-Begriff.",
        question_type=QuestionTypes.FREITEXT,
        license=License.CC_BY,
        status=Status.DRAFT,
        author_id=uuid4(),
        solution="Atomicity, Consistency, Isolation, Durability",
        item_metadata=_default_item_metadata(),
    )
    assert payload.fragestellung == "Erkläre den ACID-Begriff."


def freitext_item_create_rejects_empty_fragestellung():
    with pytest.raises(ValidationError):
        ItemCreate(
            fragestellung="   ",
            question_type=QuestionTypes.FREITEXT,
            license=License.CC_BY,
            status=Status.DRAFT,
            author_id=uuid4(),
            item_metadata=_default_item_metadata(),
        )


def freitext_item_create_rejects_object_as_fragestellung():
    with pytest.raises(ValidationError):
        ItemCreate(
            fragestellung={"prompt": "Hallo", "options": []},
            question_type=QuestionTypes.FREITEXT,
            license=License.CC_BY,
            status=Status.DRAFT,
            author_id=uuid4(),
            item_metadata=_default_item_metadata(),
        )


def freitext_item_create_solution_is_optional():
    payload = ItemCreate(
        fragestellung="Beschreibe Normalformen.",
        question_type=QuestionTypes.FREITEXT,
        license=License.CC0,
        status=Status.DRAFT,
        author_id=uuid4(),
        item_metadata=_default_item_metadata(),
    )
    assert payload.solution is None


def freitext_item_create_rejects_empty_string_solution():
    with pytest.raises(ValidationError):
        ItemCreate(
            fragestellung="Gültige Frage",
            question_type=QuestionTypes.FREITEXT,
            license=License.CC_BY,
            status=Status.DRAFT,
            author_id=uuid4(),
            solution="   ",
            item_metadata=_default_item_metadata(),
        )


def multiple_choice_item_create_accepts_valid_payload():
    options = [
        MultipleChoiceOption(option_id="a", text="Richtig"),
        MultipleChoiceOption(option_id="b", text="Falsch"),
    ]
    payload = ItemCreate(
        fragestellung=MultipleChoiceQuestionPayload(prompt="Ist 1+1=2?", options=options),
        question_type=QuestionTypes.MULTIPLECHOICE,
        license=License.CC_BY_SA,
        status=Status.DRAFT,
        author_id=uuid4(),
        solution=MultipleChoiceSolutionPayload(options=options, correct_option_ids=["a"]),
        item_metadata=_default_item_metadata(),
    )
    assert isinstance(payload.fragestellung, MultipleChoiceQuestionPayload)


def multiple_choice_item_create_rejects_plain_string_as_fragestellung():
    options = [
        MultipleChoiceOption(option_id="a", text="Ja"),
        MultipleChoiceOption(option_id="b", text="Nein"),
    ]
    with pytest.raises(ValidationError):
        ItemCreate(
            fragestellung="Einfacher Text statt Objekt",
            question_type=QuestionTypes.MULTIPLECHOICE,
            license=License.CC_BY,
            status=Status.DRAFT,
            author_id=uuid4(),
            solution=MultipleChoiceSolutionPayload(options=options, correct_option_ids=["a"]),
            item_metadata=_default_item_metadata(),
        )


def multiple_choice_item_create_rejects_mismatched_option_ids_between_fragestellung_and_solution():
    fragestellung_options = [
        MultipleChoiceOption(option_id="a", text="Ja"),
        MultipleChoiceOption(option_id="b", text="Nein"),
    ]
    solution_options = [
        MultipleChoiceOption(option_id="x", text="Ja"),
        MultipleChoiceOption(option_id="y", text="Nein"),
    ]
    with pytest.raises(ValidationError):
        ItemCreate(
            fragestellung=MultipleChoiceQuestionPayload(prompt="Frage?", options=fragestellung_options),
            question_type=QuestionTypes.MULTIPLECHOICE,
            license=License.CC_BY,
            status=Status.DRAFT,
            author_id=uuid4(),
            solution=MultipleChoiceSolutionPayload(options=solution_options, correct_option_ids=["x"]),
            item_metadata=_default_item_metadata(),
        )


def multiple_choice_item_create_rejects_plain_string_as_solution():
    options = [
        MultipleChoiceOption(option_id="a", text="Ja"),
        MultipleChoiceOption(option_id="b", text="Nein"),
    ]
    with pytest.raises(ValidationError):
        ItemCreate(
            fragestellung=MultipleChoiceQuestionPayload(prompt="Frage?", options=options),
            question_type=QuestionTypes.MULTIPLECHOICE,
            license=License.CC_BY,
            status=Status.DRAFT,
            author_id=uuid4(),
            solution="Einfacher String statt Objekt",
            item_metadata=_default_item_metadata(),
        )


def item_create_rejects_missing_bloomlevel_metadata():
    with pytest.raises(ValidationError):
        ItemCreate(
            fragestellung="Was ist SQL?",
            question_type=QuestionTypes.FREITEXT,
            license=License.CC_BY,
            status=Status.DRAFT,
            author_id=uuid4(),
            item_metadata={"punkte": 3},
        )


# ===========================================================================
# Schema-Validierung: MultipleChoiceSolutionPayload
# ===========================================================================

def multiple_choice_solution_rejects_unknown_correct_option_id():
    options = [
        MultipleChoiceOption(option_id="a", text="Ja"),
        MultipleChoiceOption(option_id="b", text="Nein"),
    ]
    with pytest.raises(ValidationError):
        MultipleChoiceSolutionPayload(options=options, correct_option_ids=["c"])


def multiple_choice_solution_rejects_duplicate_option_ids():
    options = [
        MultipleChoiceOption(option_id="a", text="Ja"),
        MultipleChoiceOption(option_id="a", text="Nein"),
    ]
    with pytest.raises(ValidationError):
        MultipleChoiceSolutionPayload(options=options, correct_option_ids=["a"])


def multiple_choice_solution_accepts_multiple_correct_option_ids():
    options = [
        MultipleChoiceOption(option_id="a", text="Eins"),
        MultipleChoiceOption(option_id="b", text="Zwei"),
        MultipleChoiceOption(option_id="c", text="Drei"),
    ]
    payload = MultipleChoiceSolutionPayload(options=options, correct_option_ids=["a", "c"])
    assert payload.correct_option_ids == ["a", "c"]


# ===========================================================================
# Enum-Endpunkte
# ===========================================================================

def test_get_all_available_fachbereiche_returns_all_enum_values(client: TestClient):
    response = client.get("/getAllAvailableFachbereiche")
    assert response.status_code == 200
    assert set(response.json()) == {f.value for f in Themenbereich}


def test_get_all_available_license_types_returns_all_enum_values(client: TestClient):
    response = client.get("/getAllAvailableLicenseTypes")
    assert response.status_code == 200
    assert set(response.json()) == {lic.value for lic in License}


def test_get_all_available_status_types_returns_all_enum_values(client: TestClient):
    response = client.get("/getAllAvailableStatusTypes")
    assert response.status_code == 200
    assert set(response.json()) == {s.value for s in Status}


def test_get_all_available_question_types_returns_all_enum_values(client: TestClient):
    response = client.get("/getAllAvailableQuestionsTypes")
    assert response.status_code == 200
    assert set(response.json()) == {qt.value for qt in QuestionTypes}


# ===========================================================================
# Organisation-Endpunkte
# ===========================================================================

def test_create_organisation_persists_and_returns_organisation(client: TestClient):
    response = client.post("/createOrganisation",
                           json={"name": "FH Test", "contact": "fh@test.de", "faculty": "Informatik"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "FH Test"
    assert "id" in data


def test_get_all_organisations_returns_empty_list_when_no_organisations_exist(client: TestClient):
    response = client.get("/getAllOrganisations")
    assert response.status_code == 200
    assert response.json() == []


def test_get_all_organisations_returns_created_organisations(client: TestClient, session: Session):
    _create_organisation(session)
    response = client.get("/getAllOrganisations")
    assert response.status_code == 200
    assert len(response.json()) == 1


# ===========================================================================
# Creator-Endpunkte
# ===========================================================================

def test_create_creator_persists_and_returns_creator(client: TestClient, session: Session):
    org = _create_organisation(session)
    payload = {"name": "Anna Beispiel", "email": "anna@uni.de", "role": 2, "organisation_id": str(org.id)}
    response = client.post("/createCreator", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Anna Beispiel"
    assert "author_id" in data


def test_get_all_creator_returns_empty_list_when_no_creators_exist(client: TestClient):
    response = client.get("/getAllCreator")
    assert response.status_code == 200
    assert response.json() == []


def test_get_all_creator_returns_creator_with_organisation_name(client: TestClient, session: Session):
    org = _create_organisation(session)
    _create_creator(session, org.id)
    response = client.get("/getAllCreator")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["organisation_name"] == "Test-Uni"
    assert data[0]["name"] == "Max Mustermann"


# ===========================================================================
# Item-Endpunkte
# ===========================================================================

def test_get_all_items_returns_empty_list_when_no_items_exist(client: TestClient):
    response = client.get("/getAllItems")
    assert response.status_code == 200
    assert response.json() == []


def test_create_item_with_freitext_persists_and_returns_item(client: TestClient, session: Session):
    org = _create_organisation(session)
    creator = _create_creator(session, org.id)

    response = client.post("/createItem", json=_freitext_item_payload(creator.author_id))

    assert response.status_code == 200
    data = response.json()
    assert data["fragestellung"] == "Was ist eine Transaktion?"
    assert data["question_type"] == QuestionTypes.FREITEXT.value
    assert data["status"] == Status.DRAFT.value
    assert data["author_id"] == str(creator.author_id)
    assert "item_id" in data


def test_create_item_returns_404_when_author_does_not_exist(client: TestClient):
    unknown_author_id = str(uuid4())
    payload = {
        "fragestellung": "Irgendeine Frage",
        "question_type": QuestionTypes.FREITEXT.value,
        "license": License.CC_BY.value,
        "status": Status.DRAFT.value,
        "author_id": unknown_author_id,
        "solution": "Irgendeine Antwort",
        "item_metadata": _default_item_metadata(),
    }
    response = client.post("/createItem", json=payload)
    assert response.status_code == 404
    assert "author_id" in response.json()["detail"]


def test_create_item_with_multiple_choice_persists_structured_payload(client: TestClient, session: Session):
    org = _create_organisation(session)
    creator = _create_creator(session, org.id)

    response = client.post("/createItem", json=_multiple_choice_payload(creator.author_id))

    assert response.status_code == 200
    data = response.json()
    assert data["question_type"] == QuestionTypes.MULTIPLECHOICE.value
    fragestellung = json.loads(data["fragestellung"])
    assert fragestellung["prompt"] == "Ist SQL eine Sprache?"


def test_create_item_with_optional_metadata_persists_metadata(client: TestClient, session: Session):
    org = _create_organisation(session)
    creator = _create_creator(session, org.id)
    payload = _freitext_item_payload(creator.author_id)
    payload["item_metadata"] = {"bloomlevel": "analyze", "schwierigkeit": "mittel", "punkte": 5}

    response = client.post("/createItem", json=payload)

    assert response.status_code == 200
    assert response.json()["item_metadata"] == {"bloomlevel": "analyze", "schwierigkeit": "mittel", "punkte": 5}


def test_create_item_defaults_status_to_draft_when_not_provided(client: TestClient, session: Session):
    org = _create_organisation(session)
    creator = _create_creator(session, org.id)
    payload = _freitext_item_payload(creator.author_id)
    del payload["status"]

    response = client.post("/createItem", json=payload)

    assert response.status_code == 200
    assert response.json()["status"] == Status.DRAFT.value


def test_get_all_items_returns_all_persisted_items(client: TestClient, session: Session):
    org = _create_organisation(session)
    creator = _create_creator(session, org.id)

    client.post("/createItem", json=_freitext_item_payload(creator.author_id))
    client.post("/createItem", json=_freitext_item_payload(creator.author_id))

    response = client.get("/getAllItems")
    assert response.status_code == 200
    assert len(response.json()) == 2


# ===========================================================================
# searchItems-Endpunkt
# ===========================================================================

def test_search_items_returns_all_items_when_no_filters_are_given(client: TestClient, session: Session):
    org = _create_organisation(session)
    creator = _create_creator(session, org.id)

    client.post("/createItem", json=_freitext_item_payload(creator.author_id))

    response = client.get("/searchItems")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert "author_name" in response.json()[0]


def test_search_items_filters_by_fragestellung_substring(client: TestClient, session: Session):
    org = _create_organisation(session)
    creator = _create_creator(session, org.id)

    payload_a = _freitext_item_payload(creator.author_id)
    payload_b = {**_freitext_item_payload(creator.author_id), "fragestellung": "Was ist ein Index?"}

    client.post("/createItem", json=payload_a)
    client.post("/createItem", json=payload_b)

    response = client.get("/searchItems", params={"q": "Transaktion"})
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert "Transaktion" in results[0]["fragestellung"]


def test_search_items_filters_by_author_id(client: TestClient, session: Session):
    org = _create_organisation(session)
    creator_a = _create_creator(session, org.id)
    creator_b = Creator(name="Andere Person", email="andere@test.de", role=1, organisation_id=org.id)
    session.add(creator_b)
    session.commit()
    session.refresh(creator_b)

    client.post("/createItem", json=_freitext_item_payload(creator_a.author_id))
    client.post("/createItem", json=_freitext_item_payload(creator_b.author_id))

    response = client.get("/searchItems", params={"author_id": str(creator_a.author_id)})
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["author_id"] == str(creator_a.author_id)


def test_search_items_filters_by_author_name(client: TestClient, session: Session):
    org = _create_organisation(session)
    creator = _create_creator(session, org.id)

    client.post("/createItem", json=_freitext_item_payload(creator.author_id))

    response = client.get("/searchItems", params={"author_name": "Muster"})
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_search_items_returns_empty_list_for_non_matching_query(client: TestClient, session: Session):
    org = _create_organisation(session)
    creator = _create_creator(session, org.id)

    client.post("/createItem", json=_freitext_item_payload(creator.author_id))

    response = client.get("/searchItems", params={"q": "GibtEsNicht"})
    assert response.status_code == 200
    assert response.json() == []


# ===========================================================================
# exportItems-Endpunkt
# ===========================================================================

def test_export_items_returns_json_file_with_all_items(client: TestClient, session: Session):
    org = _create_organisation(session)
    creator = _create_creator(session, org.id)

    client.post("/createItem", json=_freitext_item_payload(creator.author_id))

    response = client.get("/exportItems")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert "attachment" in response.headers["content-disposition"]
    assert "items_export.json" in response.headers["content-disposition"]
    exported = response.json()
    assert len(exported) == 1
    assert exported[0]["fragestellung"] == "Was ist eine Transaktion?"


def test_export_items_filters_by_fragestellung_substring(client: TestClient, session: Session):
    org = _create_organisation(session)
    creator = _create_creator(session, org.id)
    payload_other = {**_freitext_item_payload(creator.author_id), "fragestellung": "Was ist ein Join?"}

    client.post("/createItem", json=_freitext_item_payload(creator.author_id))
    client.post("/createItem", json=payload_other)

    response = client.get("/exportItems", params={"q": "Join"})
    assert response.status_code == 200
    exported = response.json()
    assert len(exported) == 1
    assert "Join" in exported[0]["fragestellung"]


def test_export_items_returns_empty_list_when_no_items_exist(client: TestClient):
    response = client.get("/exportItems")
    assert response.status_code == 200
    assert response.json() == []
