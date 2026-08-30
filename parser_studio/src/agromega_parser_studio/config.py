import json
from dataclasses import asdict, dataclass
from pathlib import Path

import keyring
from platformdirs import user_config_dir

SERVICE_NAME = "agromega-parser-studio"


@dataclass(slots=True)
class ConnectionProfile:
    name: str = "Local AgroMega"
    base_url: str = "http://localhost:8000/"

    @property
    def normalized_base_url(self) -> str:
        return self.base_url.rstrip("/") + "/"


class ProfileStore:
    def __init__(self, path: Path | None = None):
        self.path = path or Path(user_config_dir("AgroMega Parser Studio")) / "profiles.json"

    def load(self) -> list[ConnectionProfile]:
        if not self.path.exists():
            return [ConnectionProfile()]
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return [ConnectionProfile(**item) for item in data.get("profiles", [])] or [ConnectionProfile()]

    def save(self, profiles: list[ConnectionProfile]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"profiles": [asdict(profile) for profile in profiles]}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def get_token(profile: ConnectionProfile) -> str:
        return keyring.get_password(SERVICE_NAME, profile.name) or ""

    @staticmethod
    def set_token(profile: ConnectionProfile, token: str) -> None:
        if token:
            keyring.set_password(SERVICE_NAME, profile.name, token)
        else:
            try:
                keyring.delete_password(SERVICE_NAME, profile.name)
            except keyring.errors.PasswordDeleteError:
                pass
