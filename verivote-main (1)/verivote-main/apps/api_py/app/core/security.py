from app.core.config import Settings
from app.core.errors import DomainError


def ensure_demo_credential_issuer_allowed(settings: Settings) -> None:
    if not settings.allow_demo_credential_issuer:
        raise DomainError(403, "Demo credential issuer is disabled")


def ensure_mock_verifier_allowed(settings: Settings) -> None:
    if not settings.allow_mock_verifier:
        raise DomainError(403, "Mock verifier is disabled")


def ensure_zk_mock_mode_allowed(settings: Settings) -> None:
    if settings.zk_mock_mode and settings.app_mode in {"competition", "production"}:
        raise DomainError(
            403,
            "ZK mock mode is forbidden in competition or production mode",
        )
