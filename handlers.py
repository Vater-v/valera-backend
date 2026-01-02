from models import ServerPacket, AccountInfo, GameData
from session import GameSession

class PacketRouter:
    def process(self, json_data: dict, session: GameSession):
        # 1. ПРОВЕРКА НА ПРОСТОЙ ЛОГИН
        if "login" in json_data and "id" in json_data:
            session.update_hero(json_data["id"], json_data["login"])
            return

        # 2. ПАРСИНГ ПАКЕТА
        try:
            packet = ServerPacket(**json_data)
        except Exception:
            return

        # Нормализация
        payload = packet.payload
        pkt_type = packet.type

        if packet.body:
            if not pkt_type: pkt_type = packet.body.type
            if not payload: payload = packet.body.payload

        if not payload:
            return

        # --- ЛОГИКА ОБРАБОТКИ ---

        # А. Смена стадии (Lobby, GamePlay)
        if pkt_type in ["StageChanged", "StageInfo"]:
            if payload.stage:
                session.current_stage = payload.stage
                # Если вышли из игры в лобби - сбрасываем флаг
                if payload.stage == "Lobby":
                    session.is_in_game = False

            # Попытка вытащить данные героя из контекста
            if payload.context:
                acc: AccountInfo = None
                if payload.context.account_info:
                    acc = payload.context.account_info
                elif payload.context.game_offers:
                    acc = payload.context.game_offers[0].account_info

                if acc:
                    nick = acc.profile.nickname if acc.profile else None
                    session.update_hero(acc.id, acc.login, nick)

        # Б. События игры
        elif pkt_type == "StageEvent":
            event = payload.name

            # 1. Начало игры (самое важное событие)
            if event == "GameStarted":
                # data автоматически парсится в GameData благодаря Pydantic,
                # но нужно проверить, не dict ли это (на случай ошибок валидации)
                data = payload.data

                # Если вдруг пришел dict (fallback), попробуем превратить в GameData
                if isinstance(data, dict):
                    try:
                        data = GameData(**data)
                    except:
                        pass # Оставляем как dict

                # Извлекаем данные
                if isinstance(data, GameData) and data.players:
                    game_id = data.game_id
                    variant = data.variant

                    # Ставка
                    stake_val = "0"
                    currency = "chips"
                    if data.stake:
                        stake_val = data.stake.amount
                        currency = data.stake.currency

                    # Определяем оппонента (тот, кто НЕ мы)
                    opp_id = "Unknown"
                    opp_name = "Unknown"

                    # players - это словарь {"first": GamePlayer, "second": GamePlayer}
                    for key, player in data.players.items():
                        # player.user.account_id
                        p_id = player.user.account_id
                        if session.hero_id and p_id != session.hero_id:
                            opp_id = p_id
                            opp_name = player.user.username
                            break
                        # Если наш ID еще не определен, берем второго как оппонента (эвристика)
                        elif not session.hero_id and key == "second":
                             opp_id = p_id
                             opp_name = player.user.username

                    # Записываем в сессию
                    session.start_new_game(
                        game_id=game_id,
                        variant=variant,
                        stake=stake_val,
                        currency=currency,
                        opponent_id=opp_id,
                        opponent_name=opp_name
                    )

            # 2. Ваш ход (или ход оппонента)
            elif event == "TurnStarted":
                # Тут можно добавить логику проверки, чей ход
                pass

            # 3. Бросок кубиков
            elif event == "DiceRolled":
                dice = payload.data.get("firstDiceRoll") or payload.data.get("gameBoardState", {}).get("firstDice")
                if dice and session.is_in_game:
                    print(f"🎲 Кубики: {dice['first']}:{dice['second']}")
