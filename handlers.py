from models import ServerPacket, AccountInfo
from session import GameSession

class PacketRouter:
    def process(self, json_data: dict, session: GameSession):
        # 1. ПРОВЕРКА НА ПРОСТОЙ ЛОГИН (самый первый пакет)
        # Log: {"login":"Hmuriy","id":"..."}
        if "login" in json_data and "id" in json_data:
            session.update_hero(json_data["id"], json_data["login"])
            return

        # 2. ПАРСИНГ СЛОЖНОГО ПАКЕТА
        try:
            packet = ServerPacket(**json_data)
        except Exception:
            return  # Не наш формат

        # Нормализация: достаем payload откуда угодно (из корня или из body)
        payload = packet.payload
        pkt_type = packet.type

        if packet.body:
            if not pkt_type: pkt_type = packet.body.type
            if not payload: payload = packet.body.payload

        if not payload:
            return

        # --- ЛОГИКА ОБРАБОТКИ ---

        # А. Смена стадии (Lobby, ClubLobby, GamePlay)
        # В этих пакетах всегда лежат данные аккаунта
        if pkt_type in ["StageChanged", "StageInfo"]:
            if payload.stage:
                session.current_stage = payload.stage
                # print(f"🌍 [STAGE] Переход в: {payload.stage}")

            if payload.context:
                acc: AccountInfo = None

                # Вариант 1: Данные лежат прямо в контексте
                if payload.context.account_info:
                    acc = payload.context.account_info

                # Вариант 2: Данные лежат в списке gameOffers (как в твоем логе Lobby)
                elif payload.context.game_offers:
                    # Берем первый оффер, там обычно наш аккаунт
                    acc = payload.context.game_offers[0].account_info

                if acc:
                    nick = acc.profile.nickname if acc.profile else None
                    session.update_hero(acc.id, acc.login, nick)

        # Б. События игры (DiceRolled, GameStarted)
        elif pkt_type == "StageEvent":
            event = payload.name
            if event == "DiceRolled":
                dice = payload.data.get("firstDiceRoll") or payload.data.get("gameBoardState", {}).get("firstDice")
                print(f"🎲 [GAME] Кубики: {dice}")
                # Тут будет вызов функции бота: bot.calculate_move(...)

            elif event == "GameStarted":
                session.is_in_game = True
                print("⚔️ [GAME] Начало партии!")
