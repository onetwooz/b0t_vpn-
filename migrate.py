from database import Base, engine
import models.user, models.key, models.payment, models.trial_log

if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)
    print('Таблицы успешно созданы.') 