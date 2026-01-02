class GameSession:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

        self.hero_id: str | None = None
        self.hero_login: str | None = None
        self.hero_nickname: str | None = None

        self.current_stage: str = "UNKNOWN"
        self.is_in_game: bool = False

    def update_hero(self, uid: str, login: str = None, nickname: str = None):
        """Обновляет данные и выводит лог, если они изменились"""
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

    def __repr__(self):
        return f"<Session {self.ip}:{self.port} | {self.hero_login or 'Guest'}>"
