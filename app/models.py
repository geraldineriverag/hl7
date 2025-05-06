from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from typing import Optional

class Protocol(str, Enum):
    HTTP  = "http"
    HTTPS = "https"
    MLLP  = "mllp"

@dataclass
class Destination:
    id: int
    name: str
    protocol: Protocol
    host: str
    port: int
    path: str = ""
    use_tls: bool = False
    cert_path: str = ""

    def to_dict(self):
        d = asdict(self)
        d["protocol"] = self.protocol.value
        return d

@dataclass
class HL7Log:
    id: int
    dest_id: int
    message: str
    status: str
    response: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    forwarded_at: str = ""
    response_code: Optional[int] = None
    error_type: str = ""
    error_detail: str = ""
    http_status: Optional[int] = None
    parent_log_id: Optional[int] = None

    def to_dict(self):
        return asdict(self)

@dataclass
class AppConfig:
    active_dest_id: Optional[int]
    use_mtls: bool
    client_cert: str = ""
    client_key: str = ""
    ca_cert: str = ""

    def to_dict(self):
        return asdict(self)
