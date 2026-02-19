import pytest
from unittest.mock import MagicMock, patch
from backend.main import app

def test_auth_callback_success(client):
    # Mock settings
    mock_settings = MagicMock()
    mock_settings.OIDC_ISSUER = "https://mock-oidc.com"
    mock_settings.OIDC_CLIENT_ID = "test-client-id"
    mock_settings.OIDC_CLIENT_SECRET = "test-client-secret"
    mock_settings.OIDC_CALLBACK_URL = "http://localhost:8000/api/auth/callback"
    
    with patch("backend.routers.auth.settings", mock_settings):
        # Mock httpx.AsyncClient
        with patch("backend.routers.auth.httpx.AsyncClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            
            # Setup mock response for token exchange
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "access_token": "mock_access_token",
                "id_token": "mock_id_token",
                "token_type": "Bearer",
                "expires_in": 3600
            }
            mock_response.raise_for_status.return_value = None
            
            mock_client_instance.post.return_value = mock_response
            
            # Mock auth.verify_oidc_token
            with patch("backend.auth.verify_oidc_token") as mock_verify:
                mock_verify.return_value = {"email": "test@example.com"}
                
                # Mock create_access_token
                with patch("backend.auth.create_access_token") as mock_create_token:
                    mock_create_token.return_value = "internal_access_token"
                    
                    # Mock DB / CRUD
                    # We need to mock get_db dependency or crud functions
                    with patch("backend.crud.get_user_by_email") as mock_get_user:
                        mock_get_user.return_value = MagicMock(email="test@example.com", firstname="Test", lastname="User")
                        
                        # Call the endpoint
                        response = client.get("/api/auth/callback?code=valid-code&state=xyz")
                        
                        assert response.status_code == 200
                        data = response.json()
                        assert data["access_token"] == "internal_access_token"
                        assert data["user"]["email"] == "test@example.com"
                        
                        # Verify post call arguments
                        mock_client_instance.post.assert_called_once()
            call_args = mock_client_instance.post.call_args
            assert call_args[0][0] == "https://mock-oidc.com/token"
            assert call_args[1]["data"]["code"] == "valid-code"
            assert call_args[1]["data"]["client_id"] == "test-client-id"
            assert call_args[1]["data"]["client_secret"] == "test-client-secret"

def test_auth_callback_missing_config(client):
    # Mock empty settings
    mock_settings = MagicMock()
    mock_settings.OIDC_ISSUER = ""
    
    with patch("backend.routers.auth.settings", mock_settings):
        response = client.get("/api/auth/callback?code=valid-code")
        assert response.status_code == 501
        assert response.json()["detail"] == "OIDC is not configured on the backend."

def test_config_endpoint_includes_oidc(client):
    # Mock settings
    mock_settings = MagicMock()
    mock_settings.RUNORG_START_DATE = "2023-01-01"
    mock_settings.RUNORG_END_DATE = "2023-12-31"
    mock_settings.RUNORG_TOTAL_STEP_GOAL = 1000
    mock_settings.RUNORG_STEP_PER_KM = 1500
    mock_settings.RUNORG_TOP_USER = 5
    mock_settings.OIDC_ISSUER = "https://mock-oidc.com"
    mock_settings.OIDC_CLIENT_ID = "test-client"
    mock_settings.OIDC_CALLBACK_URL = "http://cb"
    
    with patch("backend.main.settings", mock_settings):
        response = client.get("/api/config")
        assert response.status_code == 200
        data = response.json()
        assert data["oidc_issuer"] == "https://mock-oidc.com"
        assert data["oidc_client_id"] == "test-client"
