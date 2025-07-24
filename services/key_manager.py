# Сервис для работы с VPN-ключами

class KeyManager:
    def __init__(self, db):
        self.db = db

    def has_recent_trial(self, user_id, server):
        from models.trial_log import TrialLog
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        month_ago = now - timedelta(days=30)
        q = self.db.query(TrialLog).filter(
            TrialLog.user_id == user_id,
            TrialLog.server == server.value,
            TrialLog.issued_at >= month_ago
        )
        return self.db.query(q.exists()).scalar()

    def issue_key(self, user_id, server, period, is_trial=False):
        from models.key import Key
        from models.trial_log import TrialLog
        from datetime import datetime, timedelta
        # Найти свободный ключ
        key = self.db.query(Key).filter_by(server=server, is_trial=is_trial, used=False).first()
        if not key:
            return None
        key.issued_to = user_id
        key.issued_at = datetime.utcnow()
        key.expires_at = key.issued_at + timedelta(days=period)
        key.used = True
        self.db.add(key)
        if is_trial:
            trial_log = TrialLog(user_id=user_id, server=server.value)
            self.db.add(trial_log)
        self.db.commit()
        self.db.refresh(key)
        return key

    def remove_expired_keys(self):
        # Логика удаления просроченных ключей
        pass

    def load_keys_from_url(self, url, server):
        import requests
        from models.key import Key, ServerLocation
        response = requests.get(url)
        if response.status_code != 200:
            return 0
        keys = [line.strip() for line in response.text.splitlines() if line.strip()]
        count = 0
        for key_str in keys:
            # Проверяем, нет ли такого ключа уже в базе
            exists = self.db.query(Key).filter_by(key=key_str).first()
            if exists:
                continue
            key = Key(key=key_str, server=ServerLocation(server), is_trial=False, used=False)
            self.db.add(key)
            count += 1
        self.db.commit()
        return count

    def delete_key(self, key_str):
        from models.key import Key
        key = self.db.query(Key).filter_by(key=key_str).first()
        if not key:
            return False
        self.db.delete(key)
        self.db.commit()
        return True 