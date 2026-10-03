from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def isolated_activities(monkeypatch):
    activities = deepcopy(app_module.activities)
    monkeypatch.setattr(app_module, "activities", activities)
    return activities


@pytest.fixture
def client(isolated_activities):
    return TestClient(app_module.app)


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_data(client, isolated_activities):
    # Arrange
    expected_activities = deepcopy(isolated_activities)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant(client, isolated_activities):
    # Arrange
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"
    participants_before = list(isolated_activities[activity_name]["participants"])

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert isolated_activities[activity_name]["participants"] == [
        *participants_before,
        email,
    ]


def test_signup_returns_not_found_for_unknown_activity(client, isolated_activities):
    # Arrange
    activity_name = "Unknown Club"
    email = "student@mergington.edu"
    activities_before = deepcopy(isolated_activities)

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
    assert isolated_activities == activities_before


def test_signup_rejects_duplicate_participant(client, isolated_activities):
    # Arrange
    activity_name = "Chess Club"
    email = isolated_activities[activity_name]["participants"][0]
    participants_before = list(isolated_activities[activity_name]["participants"])

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 409
    assert response.json()["detail"] == "Already signed up"
    assert isolated_activities[activity_name]["participants"] == participants_before


def test_signup_requires_email(client, isolated_activities):
    # Arrange
    activity_name = "Chess Club"
    participants_before = list(isolated_activities[activity_name]["participants"])

    # Act
    response = client.post(f"/activities/{activity_name}/signup")

    # Assert
    assert response.status_code == 422
    assert isolated_activities[activity_name]["participants"] == participants_before


def test_remove_participant_unregisters_student(client, isolated_activities):
    # Arrange
    activity_name = "Chess Club"
    email = isolated_activities[activity_name]["participants"][0]

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants", params={"email": email}
    )
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in isolated_activities[activity_name]["participants"]
    assert email not in activities_response.json()[activity_name]["participants"]


def test_remove_participant_returns_not_found_for_unknown_activity(
    client, isolated_activities
):
    # Arrange
    activity_name = "Unknown Club"
    email = "student@mergington.edu"
    activities_before = deepcopy(isolated_activities)

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
    assert isolated_activities == activities_before


def test_remove_participant_returns_not_found_for_unregistered_student(
    client, isolated_activities
):
    # Arrange
    activity_name = "Chess Club"
    email = "not.signed.up@mergington.edu"
    participants_before = list(isolated_activities[activity_name]["participants"])

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
    assert isolated_activities[activity_name]["participants"] == participants_before


def test_remove_participant_requires_email(client, isolated_activities):
    # Arrange
    activity_name = "Chess Club"
    participants_before = list(isolated_activities[activity_name]["participants"])

    # Act
    response = client.delete(f"/activities/{activity_name}/participants")

    # Assert
    assert response.status_code == 422
    assert isolated_activities[activity_name]["participants"] == participants_before
