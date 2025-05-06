from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class HL7Log:
    id: int
    message: str
    status: str
    response: str = ""
    created_at: str = datetime.utcnow().isoformat()
    forwarded_at: str = ""
    response_code: int = None

    def to_dict(self):
        return asdict(self)

@dataclass
class AppConfig:
    mirth_url: str
    use_mtls: bool
    client_cert: str = ""
    client_key: str = ""
    ca_cert: str = ""

    def to_dict(self) -> dict:
        return asdict(self)