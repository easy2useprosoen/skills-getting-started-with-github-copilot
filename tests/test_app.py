"""Test cases for the Mergington High School Activities API."""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_all_activities(self, client):
        """Test retrieving all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_activity_structure(self, client):
        """Test that activities have correct structure."""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)

    def test_initial_participants(self, client):
        """Test that initial participants are loaded correctly."""
        response = client.get("/activities")
        data = response.json()
        
        chess_participants = data["Chess Club"]["participants"]
        assert len(chess_participants) == 2
        assert "michael@mergington.edu" in chess_participants
        assert "daniel@mergington.edu" in chess_participants


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_successful_signup(self, client):
        """Test successful signup for an activity."""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_reflects_in_activities(self, client):
        """Test that signup adds participant to activity list."""
        client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        
        response = client.get("/activities")
        data = response.json()
        participants = data["Chess Club"]["participants"]
        
        assert "newstudent@mergington.edu" in participants
        assert len(participants) == 3

    def test_duplicate_signup_fails(self, client):
        """Test that signing up twice fails."""
        # First signup
        response1 = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Duplicate signup should fail
        response2 = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity(self, client):
        """Test signup for non-existent activity fails."""
        response = client.post(
            "/activities/Fake%20Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_signup_multiple_participants(self, client):
        """Test that multiple different participants can sign up."""
        client.post(
            "/activities/Chess%20Club/signup?email=student1@mergington.edu"
        )
        client.post(
            "/activities/Chess%20Club/signup?email=student2@mergington.edu"
        )
        
        response = client.get("/activities")
        data = response.json()
        participants = data["Chess Club"]["participants"]
        
        assert len(participants) == 4
        assert "student1@mergington.edu" in participants
        assert "student2@mergington.edu" in participants


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/participants endpoint."""

    def test_successful_unregister(self, client):
        """Test successful unregistration from an activity."""
        response = client.delete(
            "/activities/Chess%20Club/participants?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]

    def test_unregister_reflects_in_activities(self, client):
        """Test that unregistration removes participant from list."""
        client.delete(
            "/activities/Chess%20Club/participants?email=michael@mergington.edu"
        )
        
        response = client.get("/activities")
        data = response.json()
        participants = data["Chess Club"]["participants"]
        
        assert "michael@mergington.edu" not in participants
        assert len(participants) == 1
        assert "daniel@mergington.edu" in participants

    def test_unregister_nonexistent_participant(self, client):
        """Test unregistering a participant not in activity fails."""
        response = client.delete(
            "/activities/Chess%20Club/participants?email=notinactivity@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_unregister_nonexistent_activity(self, client):
        """Test unregistering from non-existent activity fails."""
        response = client.delete(
            "/activities/Fake%20Activity/participants?email=michael@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_unregister_all_participants(self, client):
        """Test that all participants can be unregistered."""
        # Get initial participants
        response = client.get("/activities")
        data = response.json()
        participants = data["Chess Club"]["participants"].copy()
        
        # Unregister each one
        for email in participants:
            response = client.delete(
                f"/activities/Chess%20Club/participants?email={email}"
            )
            assert response.status_code == 200
        
        # Verify empty
        response = client.get("/activities")
        data = response.json()
        assert len(data["Chess Club"]["participants"]) == 0

    def test_unregister_then_signup_again(self, client):
        """Test that unregistered participant can sign up again."""
        # Unregister
        client.delete(
            "/activities/Chess%20Club/participants?email=michael@mergington.edu"
        )
        
        # Sign up again
        response = client.post(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify in list
        response = client.get("/activities")
        data = response.json()
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]


class TestIntegration:
    """Integration tests combining multiple operations."""

    def test_full_workflow(self, client):
        """Test complete workflow: get activities, signup, unregister."""
        # Get initial state
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        
        # Sign up new participant
        client.post(
            "/activities/Chess%20Club/signup?email=workflow@mergington.edu"
        )
        
        response = client.get("/activities")
        after_signup = len(response.json()["Chess Club"]["participants"])
        assert after_signup == initial_count + 1
        
        # Unregister
        client.delete(
            "/activities/Chess%20Club/participants?email=workflow@mergington.edu"
        )
        
        response = client.get("/activities")
        after_unregister = len(response.json()["Chess Club"]["participants"])
        assert after_unregister == initial_count

    def test_multiple_activities_independent(self, client):
        """Test that signup/unregister in one activity doesn't affect others."""
        # Get initial counts
        response = client.get("/activities")
        chess_count = len(response.json()["Chess Club"]["participants"])
        gym_count = len(response.json()["Gym Class"]["participants"])
        
        # Sign up to Chess Club
        client.post(
            "/activities/Chess%20Club/signup?email=student@mergington.edu"
        )
        
        response = client.get("/activities")
        assert len(response.json()["Chess Club"]["participants"]) == chess_count + 1
        assert len(response.json()["Gym Class"]["participants"]) == gym_count
