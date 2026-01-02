from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field

# --- Базовые настройки ---
class BaseSchema(BaseModel):
    class Config:
        extra = "ignore"
        populate_by_name = True

# --- Данные профиля (как раньше) ---
class UserProfile(BaseSchema):
    nickname: Optional[str] = None
    country: Optional[str] = None

class AccountInfo(BaseSchema):
    id: str
    login: Optional[str] = None
    profile: Optional[UserProfile] = None

# --- Модели для ИГРЫ (Новое) ---

class GameUser(BaseSchema):
    account_id: str = Field(alias="accountId")
    username: Optional[str] = None

class GamePlayer(BaseSchema):
    """Информация об игроке внутри матча"""
    user: GameUser
    checker_color: Optional[str] = Field(None, alias="checkerColor") # "WHITE" / "BLACK"
    # Тут также может быть accountProfile, но нам обычно хватает user

class GameParams(BaseSchema):
    """Параметры игры (из контекста)"""
    variant: Optional[str] = Field(None, alias="gameVariant") # ShortGammon и т.д.
    bet: Optional[Union[float, str]] = None
    currency: Optional[str] = Field(None, alias="betAmountType")
    turn_time: Optional[int] = Field(None, alias="turnTimeSec")

class GameStake(BaseSchema):
    """Информация о ставке (из события GameStarted)"""
    amount: Optional[Union[float, str]] = Field(None, alias="initialValue")
    currency: Optional[str] = Field(None, alias="amountType")

class GameData(BaseSchema):
    """Данные, приходящие в data (например, при GameStarted)"""
    game_id: Optional[str] = Field(None, alias="gameId")
    variant: Optional[str] = Field(None, alias="gameVariant")
    # Игроки приходят в словаре {"first": ..., "second": ...}
    players: Optional[Dict[str, GamePlayer]] = None
    stake: Optional[GameStake] = None

    # Специфично для событий хода (DiceRolled, TurnStarted)
    # Можно расширять по мере необходимости

# --- Контекст (Lobby / GamePlay) ---
class GameOffer(BaseSchema):
    account_info: Optional[AccountInfo] = Field(default=None, alias="accountInfo")

class GameContext(BaseSchema):
    # Данные игрока
    account_info: Optional[AccountInfo] = Field(default=None, alias="accountInfo")
    # Лобби
    game_offers: Optional[List[GameOffer]] = Field(default=None, alias="gameOffers")
    # Параметры игры (при входе в GamePlay)
    game_params: Optional[GameParams] = Field(default=None, alias="gameParams")
    # Состояние игры (иногда прилетает тут)
    game_state: Optional[Dict[str, Any]] = Field(default=None, alias="gameState")

class PacketPayload(BaseSchema):
    stage: Optional[str] = None
    context: Optional[GameContext] = None
    name: Optional[str] = None
    # data теперь пытаемся распарсить как GameData, но если не выйдет - останется dict
    data: Optional[Union[GameData, Dict[str, Any]]] = None

# --- Структура пакета ---
class PacketBody(BaseSchema):
    type: Optional[str] = None
    payload: Optional[PacketPayload] = None

class ServerPacket(BaseSchema):
    id: Optional[int] = None
    type: Optional[str] = None
    body: Optional[PacketBody] = None
    payload: Optional[PacketPayload] = None
