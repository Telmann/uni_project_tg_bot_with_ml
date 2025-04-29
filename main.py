import asyncio
import logging
import sys
import pandas as pd
from os import getenv
from aiogram.types import FSInputFile, InputMediaDocument

from model import model_predict
from answer_data import answer

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from sqlalchemy import select, update

from db import async_session, User
from db import init_db

TOKEN = '7673012869:AAEzFDN1xbU5I5-jC79Biwe3a5gC5ZMJxx4'  # security check

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    Этот обработчик/handler получает сообщения с командой `/start`.
    """
    await message.answer(
        f"Привет, {html.bold(message.from_user.full_name)}!"
        "Введите /help чтобы узнать подробнее о доступных командах!")


@dp.message(Command(commands='help'))
async def command_tsk_handler(message: Message) -> None:
    """
    Этот обработчик/handler получает сообщения с командой `/help`.
    """
    help_text = """
                Доступные команды:
                /help - показать это сообщение
                
                Для пользователей без доступа:
                /request_access - запросить доступ к боту
                /status - проверить статус своей заявки
                
                Для пользователей с доступом:
                /send - отправить .csv файл для анализа
                /format 0|1 - изменить формат ответа (0 - без графика, 1 - с графиком)
                
                Для администраторов:
                /give_permission USER_ID - выдать доступ пользователю
                /revoke_permission USER_ID - отозвать доступ у пользователя
                /view_requests - просмотреть все запросы на доступ
                """
    await message.answer(help_text)


@dp.message(Command(commands='give_permission'))
async def command_give_perm_handler(message: Message) -> None:
    try:
        permission_to_usr_id = int(message.text.split()[1])
        usr_id = message.from_user.id

        async with async_session() as session:
            # Проверяем, является ли отправитель админом
            stmt = select(User.role).filter_by(user_id=usr_id)
            role = await session.execute(stmt)
            role = role.scalars().first()

        if role != "Admin":
            await message.answer("У вас нет прав для выполнения этой команды.")
            return

        if permission_to_usr_id:
            async with async_session() as session:
                # Проверяем, существует ли пользователь
                existing_user = await session.execute(
                    select(User).where(User.user_id == permission_to_usr_id))
                user = existing_user.scalars().first()

                if user:
                    # Обновляем существующего пользователя
                    stmt = update(User).where(User.user_id == permission_to_usr_id).values(
                        permission=True,
                        request_status='approved'
                    )
                    await session.execute(stmt)
                else:
                    # Создаем нового пользователя
                    new_usr = User(
                        user_id=permission_to_usr_id,
                        role='User',
                        permission=True,
                        request_status='approved'
                    )
                    session.add(new_usr)

                await session.commit()
                await message.answer(f"Разрешение пользователю {permission_to_usr_id} выдано успешно!")
    except (IndexError, ValueError):
        await message.answer("Используйте команду в формате: /give_permission USER_ID")


@dp.message(Command(commands='send'))
async def command_send_handler(message: Message, bot: Bot) -> None:
    usr_id = message.from_user.id

    async with async_session() as session:
        stmt = select(User.permission, User.format).filter_by(user_id=usr_id)
        res = await session.execute(stmt)
        perm, user_format = res.first() or (None, None)  # Получаем список задач
    if perm:
        file_id = message.document.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path

        # Создаем временный файл
        temp_file = f"temp_{file_id}.csv"
        await bot.download_file(file_path, destination=temp_file)

        csv_to_df = pd.read_csv(temp_file)

        csv_file_path, xls_file_path, plot_path, result_hm = answer(csv_to_df)

        reply_text = (
            f"Замечательно, я отправил вам два файла (в csv и xlsx форматах) с предсказанными значениями!\nВзгляните "
            f"ниже на интерпретацию полученных предсказаний: \n\n\nВот "
            f"среднее "
            f"значение добытой нефти за первую неделю {round(result_hm['week1_avg'], 3)}, м³\nВот минимальное значение "
            f"добытой "
            f"нефти за первую неделю {round(result_hm['week1_min'], 3)}, м³ \nВот максимальное значение добытой нефти "
            f"за "
            f"первую "
            f"неделю {round(result_hm['week1_max'], 3)}, м³ \n\n\nВот среднее значение добытой нефти за вторую неделю "
            f"{round(result_hm['week2_avg'], 3)}, м³ \nВот минимальное значение добытой нефти за вторую неделю "
            f"{round(result_hm['week2_min'], 3)}, м³ \nВот максимальное значение добытой нефти за вторую неделю "
            f"{round(result_hm['week2_max'], 3)}, м³ \n\n\nВот среднее значение добытой нефти за первый месяц {round(result_hm['month1_avg'], 3)}, м³ "
            f"\nВот минимальное значение добытой нефти за месяц {round(result_hm['month1_min'], 3)}, м³ \nВот "
            f"максимальное значение "
            f"добытой нефти за месяц {round(result_hm['month1_max'], 3)}, м³")

        # csv_to_send = FSInputFile(csv_file_path)
        # await message.answer_document(document=csv_to_send,
        #                               caption="Результаты в CSV формате")
        #
        # # Отправляем XLS файл
        # xls_to_send = FSInputFile(xls_file_path)
        # await message.answer_document(document=xls_to_send,
        #                               caption="Результаты в Excel формате")
        #
        # plot_to_send = FSInputFile(plot_path)
        # await message.answer_document(document=plot_to_send,
        #                               caption="Результаты в PNG формате")

        # Создаем медиагруппу
        media_group = [
            InputMediaDocument(media=FSInputFile(csv_file_path), caption="Результаты в CSV формате"),
            InputMediaDocument(media=FSInputFile(xls_file_path), caption="Результаты в XLSX формате"),
        ]

        if user_format:
            media_group.append(
                InputMediaDocument(media=FSInputFile(plot_path), caption="График значений в PNG формате"))

        # Отправляем текст
        await message.answer(text=reply_text)
        # Отправляем медиагруппу
        await message.answer_media_group(media=media_group)

    else:
        await message.answer("У вас нет разрешения на использование доступа!")


@dp.message(Command(commands='format'))
async def command_format_handler(message: Message) -> None:
    """
    Этот обработчик/handler получает сообщения с командой '/format'.
    /format 0 - без графика
    /format 1 - с графиком (по умолчанию)
    """

    try:
        format_value = int(message.text.split()[1])
        if format_value not in [0, 1]:
            raise ValueError
    except (IndexError, ValueError):
        await message.answer("Используйте команду в формате: /format 0 или /format 1")
        return

    usr_id = message.from_user.id

    async with async_session() as session:
        # Проверяем, есть ли пользователь и имеет ли он permission
        stmt = select(User.permission).filter_by(user_id=usr_id)
        perm = await session.execute(stmt)
        perm = perm.scalars().first()

        if not perm:
            await message.answer("У вас нет разрешения на использование бота!")
            return

        # Обновляем формат для пользователя
        stmt = update(User).where(User.user_id == usr_id).values(format=format_value)
        await session.execute(stmt)
        await session.commit()

    await message.answer(f"Формат ответа изменен: {'с графиком' if format_value else 'без графика'}")


########################################################################################################################
@dp.message(Command(commands='request_access'))
async def command_request_access_handler(message: Message) -> None:
    """Обработчик запроса доступа к боту"""
    usr_id = message.from_user.id

    async with async_session() as session:
        # Проверяем, существует ли уже пользователь
        existing_user = await session.execute(
            select(User).where(User.user_id == usr_id))
        user = existing_user.scalars().first()

        if user:
            if user.permission:
                await message.answer("У вас уже есть доступ к боту!")
                return
            elif user.request_status == 'pending':
                await message.answer("Ваша заявка уже находится в обработке.")
                return

        if not user:
            # Создаем нового пользователя с запросом доступа
            new_user = User(
                user_id=usr_id,
                role='User',
                permission=False,
                request_status='pending'
            )
            session.add(new_user)
        else:
            # Обновляем статус существующего пользователя
            user.request_status = 'pending'

        await session.commit()
        await message.answer(
            "Ваш запрос на доступ отправлен администратору. Вы можете проверить статус с помощью команды /status.")


@dp.message(Command(commands='status'))
async def command_status_handler(message: Message) -> None:
    """Обработчик проверки статуса заявки"""
    usr_id = message.from_user.id

    async with async_session() as session:
        stmt = select(User.request_status).filter_by(user_id=usr_id)
        result = await session.execute(stmt)
        status = result.scalars().first()

    if not status or status == 'none':
        await message.answer(
            "Вы еще не подавали запрос на доступ. Используйте /request_access чтобы подать заявку.")
    elif status == 'pending':
        await message.answer("Ваша заявка находится в обработке. Пожалуйста, подождите.")
    elif status == 'approved':
        await message.answer("Ваша заявка одобрена! Теперь вы можете использовать бота.")
    elif status == 'rejected':
        await message.answer("К сожалению, ваша заявка была отклонена.")


@dp.message(Command(commands='revoke_permission'))
async def command_revoke_permission_handler(message: Message) -> None:
    """Обработчик отзыва разрешения (для админа)"""
    try:
        # Проверяем, является ли отправитель админом
        usr_id = message.from_user.id

        async with async_session() as session:
            stmt = select(User.role).filter_by(user_id=usr_id)
            role = await session.execute(stmt)
            role = role.scalars().first()

        if role != "Admin":
            await message.answer("У вас нет прав для выполнения этой команды.")
            return

        # Получаем ID пользователя, у которого нужно отозвать права
        target_user_id = int(message.text.split()[1])

        async with async_session() as session:
            # Обновляем статус пользователя
            stmt = update(User).where(User.user_id == target_user_id).values(
                permission=False,
                request_status='rejected'
            )
            await session.execute(stmt)
            await session.commit()

        await message.answer(f"Права пользователя {target_user_id} успешно отозваны.")

    except (IndexError, ValueError):
        await message.answer("Используйте команду в формате: /revoke_permission USER_ID")


@dp.message(Command(commands='view_requests'))
async def command_view_requests_handler(message: Message) -> None:
    """Обработчик просмотра запросов на доступ (для админа)"""
    # Проверяем, является ли отправитель админом
    usr_id = message.from_user.id

    async with async_session() as session:
        stmt = select(User.role).filter_by(user_id=usr_id)
        role = await session.execute(stmt)
        role = role.scalars().first()

    if role != "Admin":
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    # Получаем список всех пользователей с pending статусом
    async with async_session() as session:
        stmt = select(User.user_id).filter_by(request_status='pending')
        pending_users = await session.execute(stmt)
        pending_users = pending_users.scalars().all()

    if not pending_users:
        await message.answer("Нет ожидающих запросов на доступ.")
    else:
        users_list = "\n".join([f"ID: {user_id}" for user_id in pending_users])
        await message.answer(
            f"Запросы на доступ:\n{users_list}\n\nИспользуйте /give_permission USER_ID чтобы одобрить запрос.")


# это уже чисто для запуска (нужен токен и коннект к дб)
async def main() -> None:
    await init_db()
    bot = Bot(token=TOKEN,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
