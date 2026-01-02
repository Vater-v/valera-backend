from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field

# --- Базовые настройки ---
class BaseSchema(BaseModel):
    class Config:
        # ВАЖНО: "allow" позволяет сохранять поля, которых нет в схеме (например, currentTurn)
        extra = "allow"
        populate_by_name = True

# --- Данные профиля ---
class UserProfile(BaseSchema):
    nickname: Optional[str] = None
    country: Optional[str] = None

class AccountInfo(BaseSchema):
    id: str
    login: Optional[str] = None
    profile: Optional[UserProfile] = None

# --- Модели для ИГРЫ ---

class GameUser(BaseSchema):
    account_id: str = Field(alias="accountId")
    username: Optional[str] = None

class GamePlayer(BaseSchema):
    user: GameUser
    checker_color: Optional[str] = Field(None, alias="checkerColor")

class GameParams(BaseSchema):
    variant: Optional[str] = Field(None, alias="gameVariant")
    bet: Optional[Union[float, str]] = None
    currency: Optional[str] = Field(None, alias="betAmountType")
    turn_time: Optional[int] = Field(None, alias="turnTimeSec")

class GameStake(BaseSchema):
    amount: Optional[Union[float, str]] = Field(None, alias="initialValue")
    currency: Optional[str] = Field(None, alias="amountType")

class GameData(BaseSchema):
    game_id: Optional[str] = Field(None, alias="gameId")
    variant: Optional[str] = Field(None, alias="gameVariant")
    players: Optional[Dict[str, GamePlayer]] = None
    stake: Optional[GameStake] = None
    # Благодаря extra="allow", сюда также попадут currentTurn, firstDiceRoll и т.д.

# --- Контекст ---
class GameOffer(BaseSchema):
    account_info: Optional[AccountInfo] = Field(default=None, alias="accountInfo")

class GameContext(BaseSchema):
    account_info: Optional[AccountInfo] = Field(default=None, alias="accountInfo")
    game_offers: Optional[List[GameOffer]] = Field(default=None, alias="gameOffers")
    game_params: Optional[GameParams] = Field(default=None, alias="gameParams")
    game_state: Optional[Dict[str, Any]] = Field(default=None, alias="gameState")
    # Исправление: добавляем поле для идентификации игрока при смене стадии
    game_participant_id: Optional[str] = Field(default=None, alias="gameParticipantId")

class PacketPayload(BaseSchema):
    stage: Optional[str] = None
    context: Optional[GameContext] = None
    name: Optional[str] = None
    data: Optional[Union[GameData, Dict[str, Any]]] = None

class PacketBody(BaseSchema):
    type: Optional[str] = None
    payload: Optional[PacketPayload] = None

class ServerPacket(BaseSchema):
    id: Optional[int] = None
    type: Optional[str] = None
    body: Optional[PacketBody] = None
    payload: Optional[PacketPayload] = None
