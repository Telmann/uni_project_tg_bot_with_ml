from os import getenv

from sqlalchemy import Column, Integer, BigInteger, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

DATABASE_URL = f"postgresql+asyncpg://postgres:rootroot@localhost:5432/uni_bot_ml"  # security check
admin_id = 1014344205

engine = create_async_engine(DATABASE_URL, echo=True)
metadata = MetaData()

async_session = async_sessionmaker(bind=engine,
                                   class_=AsyncSession,
                                   expire_on_commit=False)

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False)
    password = Column(Text, nullable=True)
    role = Column(Text, nullable=False)
    permission = Column(Boolean, nullable=False, default=False)  # Изменено default на False
    format = Column(Integer, nullable=False, default=1)
    request_status = Column(Text, nullable=False, default='none')  # Добавлено новое поле: 'none', 'pending', 'approved', 'rejected'


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Создаем администратора, если его еще нет
    async with async_session() as session:
        # Проверяем, существует ли уже пользователь с таким user_id
        existing_admin = await session.execute(
            User.__table__.select().where(User.user_id == admin_id))
        if not existing_admin.scalar():
            admin = User(
                user_id=admin_id,
                password=None,  # или установите пароль, если нужно
                role="Admin",
                permission=True,
                format=1)
            session.add(admin)
            await session.commit()
