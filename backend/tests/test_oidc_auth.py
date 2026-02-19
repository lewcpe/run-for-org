import pytest
from unittest.mock import MagicMock, patch
from jose import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from datetime import datetime, timedelta, timezone
from backend.main import app
from backend import models

# Helper to generate RSA key pair
def generate_rsa_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    
    start_time = datetime.now(timezone.utc)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    # Construct JWK
    # Simplified JWK for RS256. 
    # In a real scenario, we'd use a library to convert PEM to JWK components (n, e).
    # However, python-jose handling is usually flexible with PEM or JWK.
    # Let's try passing the PEM in the JWKS mocking logic of authentication if possible?
    # python-jose jwt.decode() accepts verify_key which can be a key object or string.
    # But our code extracts JWKS from response.
    # So we need to mock the JWKS response structure. 
    # For RS256, we need 'n' and 'e'.
    
    # Let's rely on python-jose to create the key? Or just use a fixed keypair for testing?
    # Actually, let's use a simpler approach: Mock the `jwt.decode` if we just want to test flow?
    # BUT user wants to verify "OIDC logic", which includes fetching keys.
    # So mocking `jwt.decode` defeats the purpose of testing key fetching.
    
    # Let's generate 'n' and 'e' properly.
    public_numbers = public_key.public_numbers()
    
    def int_to_base64(value):
        import base64
        bytes_val = value.to_bytes((value.bit_length() + 7) // 8, byteorder='big')
        return base64.urlsafe_b64encode(bytes_val).decode('utf-8').rstrip('=')

    n = int_to_base64(public_numbers.n)
    e = int_to_base64(public_numbers.e)
    
    jwk = {
        "kty": "RSA",
        "use": "sig",
        "kid": "test-key-id",
        "alg": "RS256",
        "n": n,
        "e": e
    }
    
    return private_key, jwk

@pytest.fixture
def mock_oidc_setup():
    private_key, jwk = generate_rsa_key_pair()
    
    mock_settings = MagicMock()
    mock_settings.OIDC_ISSUER = "https://mock-oidc.com"
    mock_settings.OIDC_AUDIENCE = "test-audience"
    mock_settings.OIDC_ALGORITHMS = ["RS256"]
    
    mock_discovery = {
        "issuer": "https://mock-oidc.com",
        "jwks_uri": "https://mock-oidc.com/jwks"
    }
    
    mock_jwks = {
        "keys": [jwk]
    }
    
    return private_key, mock_settings, mock_discovery, mock_jwks

def test_oidc_login_flow(client, db_session, mock_oidc_setup):
    private_key, mock_settings, mock_discovery, mock_jwks = mock_oidc_setup
    
    # Patch settings in auth module
    # Note: 'backend.auth.settings' is what we need to patch if imported as 'settings'
    # Or 'backend.config.get_settings' if 'auth.py' calls it dynamically.
    # The code in auth.py does: settings = config.get_settings() at module level.
    # So we patch 'backend.auth.settings'.
    
    with patch("backend.auth.settings", mock_settings):
        # Mock httpx.Client used for fetching JWKS
        with patch("backend.auth.httpx.Client") as MockClient:
            mock_http_client = MockClient.return_value
            
            # Setup mock responses
            # First call: discovery
            # Second call: JWKS
            
            mock_resp_discovery = MagicMock()
            mock_resp_discovery.json.return_value = mock_discovery
            mock_resp_discovery.raise_for_status.return_value = None
            
            mock_resp_jwks = MagicMock()
            mock_resp_jwks.json.return_value = mock_jwks
            mock_resp_jwks.raise_for_status.return_value = None
            
            # side_effect for get(url)
            def side_effect(url):
                if url.endswith("/.well-known/openid-configuration"):
                    return mock_resp_discovery
                elif url.endswith("/jwks"):
                    return mock_resp_jwks
                raise ValueError(f"Unexpected URL: {url}")
            
            mock_http_client.get.side_effect = side_effect
            
            # Create a valid JWT
            # jose.jwt.encode expects private key as PEM bytes or string, or Key object.
            # Let's pass the private_key object or its PEM representation.
            # Using PEM bytes is standard for python-jose with RS256.
            
            private_key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )

            token = jwt.encode(
                {
                    "sub": "user123",
                    "email": "oidc_user@example.com",
                    "aud": "test-audience",
                    "iss": "https://mock-oidc.com",
                    "iat": datetime.now(timezone.utc),
                    "exp": datetime.now(timezone.utc) + timedelta(hours=1)
                },
                private_key_pem,
                algorithm="RS256",
                headers={"kid": "test-key-id"}
            )
            
            # Call verify_oidc_token directly
            from backend.auth import verify_oidc_token
            
            claims = verify_oidc_token(token)
            
            assert claims["email"] == "oidc_user@example.com"
            assert claims["iss"] == "https://mock-oidc.com"
            
            # Verify HTTP calls were made
            assert mock_http_client.get.call_count >= 2
