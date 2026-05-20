"""Tests for configuration validation and defaults."""
import pytest
from app.core.config import Settings


class TestConfigDefaults:
    def test_project_name(self):
        s = Settings(SECRET_KEY="test", _env_file=None)
        assert s.PROJECT_NAME == "Cordis"

    def test_default_sqlite(self):
        s = Settings(SECRET_KEY="test", _env_file=None)
        assert s.USE_SQLITE is True

    def test_default_logistics_enabled(self):
        s = Settings(SECRET_KEY="test", _env_file=None)
        assert s.LOGISTICS_ENABLED is True

    def test_default_whisper_model(self):
        s = Settings(SECRET_KEY="test", _env_file=None)
        assert s.WHISPER_MODEL_SIZE == "small"

    def test_default_api_prefix(self):
        s = Settings(SECRET_KEY="test", _env_file=None)
        assert s.API_V1_STR == "/api/v1"

    def test_sqlite_uri(self):
        s = Settings(SECRET_KEY="test", USE_SQLITE=True, _env_file=None)
        assert "sqlite" in s.SQLALCHEMY_DATABASE_URI

    def test_postgres_uri(self):
        s = Settings(SECRET_KEY="test", USE_SQLITE=False, POSTGRES_PASSWORD="pw",
                     POSTGRES_USER="u", POSTGRES_SERVER="h", POSTGRES_PORT="5432", POSTGRES_DB="db",
                     _env_file=None)
        assert "postgresql" in s.SQLALCHEMY_DATABASE_URI

    def test_sqlite_blocked_in_production(self):
        with pytest.raises(RuntimeError, match="not supported in production"):
            s = Settings(SECRET_KEY="test", USE_SQLITE=True, APP_ENV="production", _env_file=None)
            _ = s.SQLALCHEMY_DATABASE_URI

    def test_allowed_origins_no_wildcard(self):
        s = Settings(SECRET_KEY="test", _env_file=None)
        assert "*" not in s.ALLOWED_ORIGINS

    def test_max_audio_bytes(self):
        s = Settings(SECRET_KEY="test", _env_file=None)
        assert s.MAX_AUDIO_BYTES == 25 * 1024 * 1024

    def test_max_transcript_length(self):
        s = Settings(SECRET_KEY="test", _env_file=None)
        assert s.MAX_TRANSCRIPT_LENGTH == 10_000

    def test_gemini_model_default(self):
        s = Settings(SECRET_KEY="test", _env_file=None)
        assert "gemini" in s.GEMINI_MODEL.lower()

    def test_vertex_ai_not_used_without_project(self):
        s = Settings(SECRET_KEY="test", _env_file=None)
        assert s.use_vertex_ai is False

    def test_vertex_ai_used_with_project(self):
        s = Settings(SECRET_KEY="test", VERTEX_AI_PROJECT="my-project", _env_file=None)
        assert s.use_vertex_ai is True


class TestConfigSecurity:
    def test_access_token_expiry_reasonable(self):
        s = Settings(SECRET_KEY="test", _env_file=None)
        assert 30 <= s.ACCESS_TOKEN_EXPIRE_MINUTES <= 1440

    def test_rate_limit_exists(self):
        """Rate limiting should be configured."""
        from app.core.security import limiter
        assert limiter is not None

    def test_jwt_algorithm(self):
        from app.core.security import ALGORITHM
        assert ALGORITHM == "HS256"
