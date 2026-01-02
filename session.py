class GameSession:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

        # Данные героя (нашего бота/игрока)
        self.hero_id: str | None = None
        self.hero_login: str | None = None
        self.hero_nickname: str | None = None

        # Текущая стадия
        self.current_stage: str = "UNKNOWN"
        self.is_in_game: bool = False

        # Состояние текущей партии (если is_in_game = True)
        self.game_id: str | None = None
        self.game_variant: str | None = None
        self.stake_amount: str | float | None = None
        self.stake_currency: str | None = None

        # Данные оппонента
        self.opponent_id: str | None = None
        self.opponent_name: str | None = None

    def update_hero(self, uid: str, login: str = None, nickname: str = None):
        """Обновляет данные героя и выводит лог при изменении."""
        changed = False
        if uid and self.hero_id != uid:
            self.hero_id = uid
            changed = True
        if login and self.hero_login != login:
            self.hero_login = login
            changed = True
        if nickname and self.hero_nickname != nickname:
            self.hero_nickname = nickname
            changed = True

        if changed:
            print(f"✅ [SESSION] Игрок определен: {self.hero_login} (Nick: {self.hero_nickname}) ID: {self.hero_id}")

    def start_new_game(self, game_id, variant, stake, currency, opponent_id, opponent_name):
        """Инициализирует новую игру."""
        self.is_in_game = True
        self.game_id = game_id
        self.game_variant = variant
        self.stake_amount = stake
        self.stake_currency = currency
        self.opponent_id = opponent_id
        self.opponent_name = opponent_name

        # Красивый вывод
        print("\n" + "="*40)
        print(f"🚀 НАЧАЛАСЬ НОВАЯ ИГРА: {variant}")
        print(f"💰 Ставка: {stake} {currency}")
        print(f"👤 Оппонент: {opponent_name} (ID: {opponent_id})")
        print("="*40 + "\n")

    def __repr__(self):
        status = f"In Game ({self.game_variant})" if self.is_in_game else "Idle"
        return f"<Session {self.hero_login or 'Guest'} | {status}>"
