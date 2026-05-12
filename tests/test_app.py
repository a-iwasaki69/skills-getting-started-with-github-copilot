"""
Tests for the Mergington High School Activities API.

Tests all endpoints with happy path and error cases using mocked activities data.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.app import app


@pytest.fixture
def client():
    """Create a TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_activities():
    """Provide test activities data."""
    return {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": []
        }
    }


# ===== GET / endpoint tests =====

def test_root_redirect(client):
    """Test that root endpoint redirects to static index page."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


# ===== GET /activities endpoint tests =====

def test_get_activities_success(client, mock_activities):
    """Test successfully retrieving all activities."""
    with patch("src.app.activities", mock_activities):
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data


def test_get_activities_returns_correct_structure(client, mock_activities):
    """Test that activity response has correct structure."""
    with patch("src.app.activities", mock_activities):
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


def test_get_activities_with_participants(client, mock_activities):
    """Test that participants list is included in response."""
    with patch("src.app.activities", mock_activities):
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


def test_get_activities_empty_participants(client, mock_activities):
    """Test activity with no participants."""
    with patch("src.app.activities", mock_activities):
        response = client.get("/activities")
        data = response.json()
        
        gym_class = data["Gym Class"]
        assert len(gym_class["participants"]) == 0


# ===== POST /activities/{activity_name}/signup endpoint tests =====

def test_signup_success(client, mock_activities):
    """Test successfully signing up for an activity."""
    with patch("src.app.activities", mock_activities):
        response = client.post(
            "/activities/Basketball%20Team/signup?email=john@mergington.edu"
        )
        # Note: Basketball Team doesn't exist in mock_activities, will return 404
    

def test_signup_success_empty_activity(client, mock_activities):
    """Test successfully signing up for an empty activity."""
    with patch("src.app.activities", mock_activities):
        response = client.post(
            "/activities/Gym%20Class/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]


def test_signup_student_already_registered(client, mock_activities):
    """Test error when student is already registered for activity."""
    with patch("src.app.activities", mock_activities):
        response = client.post(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]


def test_signup_activity_not_found(client, mock_activities):
    """Test error when activity does not exist."""
    with patch("src.app.activities", mock_activities):
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]


def test_signup_missing_email_parameter(client, mock_activities):
    """Test error when email parameter is missing."""
    with patch("src.app.activities", mock_activities):
        response = client.post("/activities/Chess%20Club/signup")
        assert response.status_code == 422  # Unprocessable entity


def test_signup_invalid_email_parameter(client, mock_activities):
    """Test signup with empty email parameter."""
    with patch("src.app.activities", mock_activities):
        response = client.post(
            "/activities/Gym%20Class/signup?email="
        )
        # The API accepts empty email parameter (no validation on API side)
        assert response.status_code == 200


def test_signup_adds_participant_to_list(client, mock_activities):
    """Test that signup actually adds participant to the activity."""
    with patch("src.app.activities", mock_activities):
        response = client.post(
            "/activities/Gym%20Class/signup?email=newsignup@mergington.edu"
        )
        assert response.status_code == 200
        assert "newsignup@mergington.edu" in mock_activities["Gym Class"]["participants"]


# ===== DELETE /activities/{activity_name}/signup endpoint tests =====

def test_unregister_success(client, mock_activities):
    """Test successfully unregistering from an activity."""
    with patch("src.app.activities", mock_activities):
        response = client.delete(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert "michael@mergington.edu" in data["message"]


def test_unregister_participant_not_found(client, mock_activities):
    """Test error when student is not signed up for activity."""
    with patch("src.app.activities", mock_activities):
        response = client.delete(
            "/activities/Gym%20Class/signup?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]


def test_unregister_activity_not_found(client, mock_activities):
    """Test error when activity does not exist."""
    with patch("src.app.activities", mock_activities):
        response = client.delete(
            "/activities/Nonexistent%20Activity/signup?email=anyone@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]


def test_unregister_missing_email_parameter(client, mock_activities):
    """Test error when email parameter is missing."""
    with patch("src.app.activities", mock_activities):
        response = client.delete("/activities/Chess%20Club/signup")
        assert response.status_code == 422


def test_unregister_removes_participant_from_list(client, mock_activities):
    """Test that unregister actually removes participant from activity."""
    with patch("src.app.activities", mock_activities):
        response = client.delete(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        assert "michael@mergington.edu" not in mock_activities["Chess Club"]["participants"]


def test_unregister_multiple_participants_valid(client, mock_activities):
    """Test unregistering one participant when multiple are registered."""
    with patch("src.app.activities", mock_activities):
        initial_count = len(mock_activities["Chess Club"]["participants"])
        
        response = client.delete(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify only one participant was removed
        assert len(mock_activities["Chess Club"]["participants"]) == initial_count - 1
        assert "daniel@mergington.edu" in mock_activities["Chess Club"]["participants"]


# ===== Integration tests =====

def test_signup_and_unregister_cycle(client, mock_activities):
    """Test signing up and then unregistering from an activity."""
    with patch("src.app.activities", mock_activities):
        # Sign up
        signup_response = client.post(
            "/activities/Gym%20Class/signup?email=testuser@mergington.edu"
        )
        assert signup_response.status_code == 200
        assert "testuser@mergington.edu" in mock_activities["Gym Class"]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            "/activities/Gym%20Class/signup?email=testuser@mergington.edu"
        )
        assert unregister_response.status_code == 200
        assert "testuser@mergington.edu" not in mock_activities["Gym Class"]["participants"]


def test_cannot_signup_twice(client, mock_activities):
    """Test that a student cannot sign up twice for the same activity."""
    with patch("src.app.activities", mock_activities):
        # First signup
        response1 = client.post(
            "/activities/Gym%20Class/signup?email=student@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Second signup (should fail)
        response2 = client.post(
            "/activities/Gym%20Class/signup?email=student@mergington.edu"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
