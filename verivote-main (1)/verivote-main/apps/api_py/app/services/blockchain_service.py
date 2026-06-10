from app.core.config import Settings


class BlockchainService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def status(self) -> dict:
        return {
            "allow_mock_verifier": self.settings.allow_mock_verifier,
            "message": "Blockchain audit service is a Python baseline placeholder",
        }

