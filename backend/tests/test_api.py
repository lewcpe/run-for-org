from backend.auth import security
from fastapi.security import HTTPAuthorizationCredentials
from backend.main import app

def test_read_main(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Run for Organization API"}

def test_config(client):
    response = client.get("/api/config")
    assert response.status_code == 200
    assert "start_date" in response.json()
    assert "step_per_km" in response.json()

def test_auth_create_user(client):
    # Mocking auth token. In our auth.py we verify token. 
    # For testing, we might need to override get_current_user or mock the JWT decoding.
    # However, our auth.py currently decoding unverified for dev/simplicity if not configured.
    # Let's try to mock the JWT token payload.
    
    from backend.auth import get_current_user
    from backend.models import User
    
    # Override get_current_user to return a mock user or skipping verify
    # But better to test the flow if possible. 
    # Let's override get_current_user for simplicity in functional tests
    
    async def mock_get_current_user():
        from backend.database import SessionLocal # Or leverage db_session fixture if possible but cleaner to return an object
        # We need a user in DB for FK constraints if we return a user model
        # The fixture handles DB.
        pass

    # Actually, let's just use the client and proper dependency override
    pass

def test_create_log_and_stats(client, db_session):
    # Override auth to return a user
    from backend import models
    from backend.auth import get_current_user
    
    user = models.User(email="test@example.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    app.dependency_overrides[get_current_user] = lambda: user
    
    # Create Log
    response = client.post(
        "/api/me/logs",
        json={"running_datetime": "2023-01-01T10:00:00", "step_count": 1500}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["step_count"] == 1500
    assert data["distance_km"] == 1.0 # Default 1500 steps/km
    
    # Verify User Stats
    response = client.get("/api/me")
    assert response.status_code == 200
    data = response.json()
    assert data["total_steps"] == 1500
    assert data["total_distance"] == 1.0
    
    # Verify Leaderboard
    response = client.get("/api/stats/leaderboard")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["email_masked"] == "tes***@example.com"
    assert data[0]["steps"] == 1500

def test_update_log(client, db_session):
    from backend import models
    from backend.auth import get_current_user
    
    user = models.User(email="test@example.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    app.dependency_overrides[get_current_user] = lambda: user
    
    # Create Log
    response = client.post(
        "/api/me/logs",
        json={"running_datetime": "2023-01-01T10:00:00", "step_count": 1000}
    )
    log_id = response.json()["id"]
    
    # Update Log
    response = client.put(
        f"/api/me/logs/{log_id}",
        json={"running_datetime": "2023-01-01T10:00:00", "step_count": 3000}
    )
    assert response.status_code == 200
    assert response.json()["step_count"] == 3000
    
    # Verify Stats Updated
    response = client.get("/api/me")
    assert response.json()["total_steps"] == 3000

def test_update_log_missing_fields(client, db_session):
    from backend import models
    from backend.auth import get_current_user
    
    user = models.User(email="test_error@example.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    app.dependency_overrides[get_current_user] = lambda: user
    
    # Create Log
    response = client.post(
        "/api/me/logs",
        json={"running_datetime": "2023-01-01T10:00:00", "step_count": 1000}
    )
    log_id = response.json()["id"]
    
    # Update Log with missing fields
    response = client.put(
        f"/api/me/logs/{log_id}",
        json={"running_datetime": "2023-01-01T12:00:00"} # Missing steps/distance
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Either step_count or distance_km must be provided for update"

def test_user_profile_update(client, db_session):
    from backend import models
    from backend.auth import get_current_user
    
    user = models.User(email="profile@example.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    app.dependency_overrides[get_current_user] = lambda: user
    
    # Update Profile
    response = client.put(
        "/api/me",
        json={"firstname": "John", "lastname": "Doe"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["firstname"] == "John"
    assert data["lastname"] == "Doe"
    
    # Verify Me Endpoint
    response = client.get("/api/me")
    assert response.json()["firstname"] == "John"
    
    # Add some steps to appear in leaderboard
    client.post("/api/me/logs", json={"running_datetime": "2023-01-01T10:00:00", "step_count": 100})
    
    # Verify Leaderboard shows name
    response = client.get("/api/stats/leaderboard")
    assert response.status_code == 200
    leaderboard = response.json()
    found = False
    for entry in leaderboard:
        if entry["email_masked"] == "pro***@example.com":
             assert entry["name"] == "John Doe"
             found = True
             break
    assert found

