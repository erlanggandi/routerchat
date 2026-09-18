from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class RouterCreateSchema(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "kantor-pusat"})
    host: str = Field(..., json_schema_extra={"example": "192.168.88.1"})
    port: int = Field(8728, json_schema_extra={"example": 8728})
    username: str = Field(..., json_schema_extra={"example": "admin"})
    password: str = Field(..., json_schema_extra={"example": "Rahasia123"})
    use_ssl: bool = Field(False, json_schema_extra={"example": False})
    description: Optional[str] = Field(None, json_schema_extra={"example": "Router Core Kantor"})


class RouterOutSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    host: str
    port: int
    username: str
    use_ssl: bool
    description: Optional[str]
    is_active: bool


class ChatRequestSchema(BaseModel):
    message: str = Field(..., json_schema_extra={"example": "Berapa penggunaan CPU router sekarang?"})
    router_id: Optional[int] = Field(None, description="ID router target. Jika null, menggunakan router aktif.")
    user_id: int = Field(1, description="ID pengguna pemanggil (misal ID user Hermes/Telegram).")
    send_to_telegram: bool = Field(False, description="Jika true, hasil/grafik juga dikirim ke grup Telegram.")


class ChatResponseSchema(BaseModel):
    reply: str
    router_name: str
    pending_approvals: List[Dict[str, Any]] = []


class ApprovalActionSchema(BaseModel):
    user_id: int = Field(..., json_schema_extra={"example": 123456})
    reason: Optional[str] = None


class NotifyMessageSchema(BaseModel):
    text: str
    chat_id: Optional[str] = None
