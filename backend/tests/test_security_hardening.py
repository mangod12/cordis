"""Security hardening tests — verify security controls are in place."""
import pytest


class TestJWTSecurity:
    def test_jwt_uses_hs256(self):
        from app.core.security import ALGORITHM
        assert ALGORITHM == "HS256"

    def test_token_creation_requires_subject(self):
        from app.core.security import create_access_token
        token = create_access_token("user-1", tenant_id="t1", role="admin")
        assert isinstance(token, str)
        assert len(token) > 50  # JWT should be substantial

    def test_password_hashing_uses_bcrypt(self):
        from app.core.security import get_password_hash, verify_password
        hashed = get_password_hash("TestPassword123!")
        assert hashed.startswith("$2b$")  # bcrypt prefix
        assert verify_password("TestPassword123!", hashed)
        assert not verify_password("WrongPassword", hashed)


class TestInputValidation:
    def test_audio_types_restricted(self):
        from app.core.config import settings
        allowed = settings.ALLOWED_AUDIO_TYPES
        assert "audio/wav" in allowed
        assert "audio/mpeg" in allowed
        # Dangerous types should NOT be allowed
        assert "application/javascript" not in allowed
        assert "text/html" not in allowed
        assert "application/x-executable" not in allowed

    def test_max_audio_size_reasonable(self):
        from app.core.config import settings
        # Should be between 1MB and 100MB
        assert 1_000_000 < settings.MAX_AUDIO_BYTES < 100_000_000

    def test_transcript_length_limited(self):
        from app.core.config import settings
        assert settings.MAX_TRANSCRIPT_LENGTH <= 50_000

    def test_cors_no_wildcard(self):
        from app.core.config import settings
        assert "*" not in settings.ALLOWED_ORIGINS


class TestSecurityHeaders:
    def test_security_middleware_importable(self):
        from app.middleware.security_headers import SecurityHeadersMiddleware
        assert SecurityHeadersMiddleware is not None

    def test_rate_limiter_configured(self):
        from app.core.security import limiter
        assert limiter is not None


class TestDatabaseSecurity:
    def test_sqlite_blocked_in_production(self):
        from app.core.config import Settings
        with pytest.raises(RuntimeError):
            s = Settings(SECRET_KEY="test", USE_SQLITE=True, APP_ENV="production")
            _ = s.SQLALCHEMY_DATABASE_URI
