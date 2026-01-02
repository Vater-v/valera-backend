from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

# --- Базовые настройки ---
class BaseSchema(BaseModel):
    class Config:
        extra = "ignore"  # Игнорируем всё лишнее, чтобы не падало

# --- Части данных игрока ---
class UserProfile(BaseSchema):
    nickname: Optional[str] = None
    country: Optional[str] = None

class AccountInfo(BaseSchema):
    id: str
    login: Optional[str] = None
    profile: Optional[UserProfile] = None

# --- Контекст игры (где лежат данные) ---
class GameOffer(BaseSchema):
    # В лобби данные игрока часто лежат внутри предложений игры
    account_info: Optional[AccountInfo] = Field(default=None, alias="accountInfo")

class GameContext(BaseSchema):
    # Прямое вложение (например, при входе в игру)
    account_info: Optional[AccountInfo] = Field(default=None, alias="accountInfo")
    # Вложение в лобби (список столов)
    game_offers: Optional[List[GameOffer]] = Field(default=None, alias="gameOffers")

class PacketPayload(BaseSchema):
    stage: Optional[str] = None
    context: Optional[GameContext] = None
    name: Optional[str] = None  # Для событий (DiceRolled и т.д.)
    data: Optional[Dict[str, Any]] = None

# --- Структура пакета ---
class PacketBody(BaseSchema):
    type: Optional[str] = None
    payload: Optional[PacketPayload] = None

class ServerPacket(BaseSchema):
    id: Optional[int] = None
    # Тип может быть в корне или внутри body
    type: Optional[str] = None
    body: Optional[PacketBody] = None
    payload: Optional[PacketPayload] = None  # Для "плоских" пакетов
