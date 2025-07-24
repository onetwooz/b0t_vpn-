# Сервис для работы с пользователями

class UserManager:
    def __init__(self, db):
        self.db = db

    def get_or_create_user(self, telegram_id, username, full_name):
        user = self.db.query(self.db.User).filter_by(telegram_id=telegram_id).first()
        if not user:
            from models.user import User
            user = User(telegram_id=telegram_id, username=username, full_name=full_name)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        return user 