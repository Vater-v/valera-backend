from models import ServerPacket, AccountInfo, GameData
from session import GameSession

class PacketRouter:
    def to_dict(self, obj):
        """Безопасно превращает Pydantic модель или dict в dict."""
        if isinstance(obj, dict):
            return obj
        if hasattr(obj, "model_dump"): # Pydantic v2
            return obj.model_dump()
        if hasattr(obj, "dict"): # Pydantic v1
            return obj.dict()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return {}

    def check_turn_state(self, data: dict, session: GameSession):
        """Анализирует состояние хода и выводит уведомления."""
        if not session.is_in_game:
            return

        current_turn = data.get("currentTurn")
        if not current_turn:
            # Иногда turn лежит внутри gameState (например, при реконнекте)
            game_state = data.get("gameState")
            if game_state:
                current_turn = game_state.get("currentTurn")

        if not current_turn:
            return

        # Определяем, чей ход
        owner_id = current_turn.get("ownerId") or current_turn.get("actionsActorId")
        is_my_turn = (owner_id == session.hero_id)

        phase = current_turn.get("phase", "UNKNOWN")
        actions = current_turn.get("availableActions", [])

        # --- ЛОГИКА ОТОБРАЖЕНИЯ ---
        if is_my_turn:
            print(f"\n🔔 >>> ВАШ ХОД! (Фаза: {phase}) <<<")

            if "RollDice" in actions:
                print("   🎲 НЕОБХОДИМО БРОСИТЬ КУБИКИ!")

            if "DoublingOffer" in actions:
                print("   🔥 ДОСТУПЕН ДАБЛ (УДВОЕНИЕ)!")

            if "MoveChecker" in actions or phase == "CHECKERS_MOVEMENT":
                print("   ♟  ХОДИТЕ ШАШКАМИ")

            if "TurnCommit" in actions:
                print("   ✅ ПОДТВЕРДИТЕ ХОД (COMMIT)")

            if not actions and phase == "DOUBLING":
                # Иногда actions пуст, но фаза удваивания требует ответа на дабл
                print("   ⚠️  ЖДУТ РЕШЕНИЯ ПО ДАБЛУ (ПРИНЯТЬ/СДАТЬСЯ)")

            # Отладочный вывод действий
            # print(f"   [Debug] Доступно: {actions}")
            print("-" * 30)

        else:
            # Ход оппонента (можно раскомментировать, если нужно следить)
            # print(f"⏳ Ход оппонента... ({phase})")
            pass

    def process(self, json_data: dict, session: GameSession):
        # 1. ПРОВЕРКА НА ПРОСТОЙ ЛОГИН
        if "login" in json_data and "id" in json_data:
            session.update_hero(json_data["id"], json_data["login"])
            return

        # 2. ПАРСИНГ ПАКЕТА
        try:
            packet = ServerPacket(**json_data)
        except Exception as e:
            # print(f"Parse error: {e}")
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
                if payload.stage == "Lobby":
                    session.is_in_game = False

            # Данные пользователя
            if payload.context:
                acc: AccountInfo = None
                if payload.context.account_info:
                    acc = payload.context.account_info
                elif payload.context.game_offers:
                    acc = payload.context.game_offers[0].account_info

                if acc:
                    nick = acc.profile.nickname if acc.profile else None
                    session.update_hero(acc.id, acc.login, nick)

                # Исправление: если нет полного профиля, берем ID из gameParticipantId
                elif payload.context.game_participant_id:
                    session.update_hero(uid=payload.context.game_participant_id)

                # Если мы подключились к игре (реконнект), проверим ситуацию
                if payload.context.game_state:
                    self.check_turn_state(payload.context.game_state, session)

        # Б. События игры
        elif pkt_type == "StageEvent":
            event = payload.name

            # Превращаем data в словарь, чтобы не ловить ошибки .get()
            raw_data = self.to_dict(payload.data) if payload.data else {}

            # 1. Начало игры
            if event == "GameStarted":
                # Попробуем распарсить через модель для удобства, но для логики используем dict
                data_obj = payload.data

                # Логика определения оппонента
                if isinstance(data_obj, GameData) and data_obj.players:
                    game_id = data_obj.game_id
                    variant = data_obj.variant

                    stake_val = "0"
                    currency = "chips"
                    if data_obj.stake:
                        stake_val = data_obj.stake.amount
                        currency = data_obj.stake.currency

                    opp_id = "Unknown"
                    opp_name = "Unknown"

                    for key, player in data_obj.players.items():
                        p_id = player.user.account_id
                        if session.hero_id and p_id != session.hero_id:
                            opp_id = p_id
                            opp_name = player.user.username
                            break
                        elif not session.hero_id and key == "second":
                             opp_id = p_id
                             opp_name = player.user.username

                    session.start_new_game(
                        game_id=game_id,
                        variant=variant,
                        stake=stake_val,
                        currency=currency,
                        opponent_id=opp_id,
                        opponent_name=opp_name
                    )

                # Сразу проверяем, чей первый ход
                self.check_turn_state(raw_data, session)

            # 2. Ход перешел или изменился
            elif event in ["TurnStarted", "TurnCheckerMovedV2", "TurnCommitted", "DoublingOffer"]:
                self.check_turn_state(raw_data, session)

            # 3. Бросок кубиков
            elif event == "DiceRolled":
                # Теперь raw_data - это словарь, .get работает безопасно
                dice = raw_data.get("firstDiceRoll") or raw_data.get("gameBoardState", {}).get("firstDice")

                # Бывает, что dice лежат в корне data (зависит от версии протокола)
                if not dice and "dice" in raw_data:
                    dice = raw_data["dice"]

                if dice and session.is_in_game:
                    d1 = dice.get('first')
                    d2 = dice.get('second')
                    print(f"🎲 Кубики выпали: {d1}:{d2}")

                # После броска нужно проверить, что делать дальше (ходить)
                self.check_turn_state(raw_data, session)

            # 4. Конец игры
            elif event == "GameFinished":
                session.is_in_game = False
                winner = raw_data.get("gameResult", {}).get("winner", {}).get("accountInfo", {}).get("nickname", "Unknown")
                print(f"\n🏁 ИГРА ОКОНЧЕНА. Победитель: {winner}\n")
