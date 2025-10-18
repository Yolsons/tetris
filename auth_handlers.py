import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from states import AuthStates
from services.auth_service import AuthService
from utils.keyboards import get_start_keyboard, get_yes_no_keyboard
from config import ADMIN_ID

logger = logging.getLogger(__name__)
auth_router = Router()

@auth_router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    """Enhanced start command handler with comprehensive user flow"""
    await state.clear()
    user_id = message.from_user.id
    
    logger.info(f"Start command from user {user_id} (@{message.from_user.username})")
    
    try:
        # Check if user is blacklisted
        if AuthService.is_user_blacklisted(user_id):
            await message.answer(
                "❌ <b>Доступ заблокирован</b>\n\n"
                "Ваш аккаунт заблокирован администратором.\n"
                "Для получения информации обратитесь к администратору.",
                parse_mode="HTML"
            )
            logger.warning(f"Blocked user attempt: {user_id}")
            return
        
        # Check if user is registered
        if AuthService.is_user_registered(user_id):
            await message.answer(
                "🎯 <b>Добро пожаловать в бот для генерации журналов инструктажей!</b>\n\n"
                "📋 Этот бот поможет вам:\n"
                "• Управлять данными компаний\n"
                "• Добавлять подразделения и инструкторов\n"
                "• Генерировать журналы инструктажей\n\n"
                "Выберите действие:",
                reply_markup=get_start_keyboard(user_id, ADMIN_ID),
                parse_mode="HTML"
            )
        else:
            await message.answer(
                "👋 <b>Добро пожаловать!</b>\n\n"
                "🔐 Для работы с ботом необходима авторизация.\n\n"
                "📩 Введите токен доступа:",
                parse_mode="HTML"
            )
            await state.set_state(AuthStates.waiting_for_token)
            
    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        await message.answer(
            "❌ Произошла ошибка при запуске.\n"
            "Попробуйте позже или обратитесь к администратору."
        )

@auth_router.message(AuthStates.waiting_for_token)
async def process_token(message: Message, state: FSMContext):
    """Enhanced token processing with detailed validation and feedback"""
    token = message.text.strip() if message.text else ""
    user_id = message.from_user.id
    
    logger.info(f"Token validation attempt from user {user_id}")
    
    # Basic token validation
    if not token:
        await message.answer(
            "❌ Токен не может быть пустым.\n\n"
            "📩 Введите корректный токен доступа:"
        )
        return
    
    if len(token) < 8:
        await message.answer(
            "❌ Токен слишком короткий.\n\n"
            "📩 Введите корректный токен доступа:"
        )
        return
    
    try:
        # Validate token
        if not AuthService.validate_token(token):
            await message.answer(
                "❌ <b>Неверный токен доступа</b>\n\n"
                "Проверьте правильность введенного токена и попробуйте снова:\n\n"
                "💡 <i>Токен должен быть получен от администратора</i>",
                parse_mode="HTML"
            )
            logger.warning(f"Invalid token attempt from user {user_id}: {token[:4]}...")
            return
        
        # Use token and create user
        token_used = AuthService.use_token(token, user_id)
        ok, created_new = AuthService.create_user(user_id, 
                                              username=message.from_user.username,
                                              first_name=message.from_user.first_name)
        
        if token_used and ok:
            # For new users, ask display name (admin defaults to "Создатель")
            if created_new:
                from config import ADMIN_ID
                if ADMIN_ID and user_id == ADMIN_ID:
                    AuthService.set_user_name(user_id, "Создатель")
                else:
                    await message.answer("Как к вам обращаться? Напишите ваше имя.")
                    await state.set_state(AuthStates.waiting_for_name)
                    return
            await message.answer(
                "✅ <b>Авторизация успешна!</b>\n\n"
                "🎉 Добро пожаловать в бот для генерации журналов инструктажей!\n\n"
                "📋 Теперь вы можете:\n"
                "• Добавлять компании и их данные\n"
                "• Генерировать документы инструктажей\n"
                "• Управлять своими данными\n\n"
                "Выберите действие:",
                reply_markup=get_start_keyboard(user_id, ADMIN_ID),
                parse_mode="HTML"
            )
            await state.clear()
            logger.info(f"User {user_id} successfully authorized with token {token[:4]}...")
        else:
            await message.answer(
                "❌ <b>Ошибка авторизации</b>\n\n"
                "Произошла ошибка при обработке токена.\n"
                "Попробуйте снова или обратитесь к администратору.",
                parse_mode="HTML"
            )
            logger.error(f"Authorization error for user {user_id}: token_used={token_used}, user_created={user_created}")
            
    except Exception as e:
        logger.error(f"Error processing token for user {user_id}: {e}")
        await message.answer(
            "❌ Произошла ошибка при авторизации.\n"
            "Попробуйте позже или обратитесь к администратору."
        )

@auth_router.message(Command("myid"))
async def get_my_id(message: Message):
    """Get user's Telegram ID with enhanced formatting"""
    user = message.from_user
    
    user_info = f"🆔 <b>Ваша информация:</b>\n\n"
    user_info += f"📱 Telegram ID: <code>{user.id}</code>\n"
    
    if user.username:
        user_info += f"👤 Username: @{user.username}\n"
    
    if user.first_name:
        user_info += f"📝 Имя: {user.first_name}"
        if user.last_name:
            user_info += f" {user.last_name}"
        user_info += "\n"
    
    user_info += f"\n💡 <i>Эта информация может потребоваться администратору</i>"
    
    await message.answer(user_info, parse_mode="HTML")

@auth_router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Return to main menu with user validation"""
    await callback.answer()
    await state.clear()
    
    user_id = callback.from_user.id
    
    try:
        if not AuthService.is_user_registered(user_id):
            await callback.message.edit_text(
                "❌ <b>Необходима авторизация</b>\n\n"
                "Используйте команду /start для начала работы.",
                parse_mode="HTML"
            )
            return
        
        if AuthService.is_user_blacklisted(user_id):
            await callback.message.edit_text(
                "❌ <b>Доступ заблокирован</b>\n\n"
                "Обратитесь к администратору.",
                parse_mode="HTML"
            )
            return
        
        await callback.message.edit_text(
            "🏠 <b>Главное меню</b>\n\n"
            "Выберите действие:",
            reply_markup=get_start_keyboard(user_id, ADMIN_ID),
            parse_mode="HTML"
        )
        
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            pass
        else:
            logger.error(f"Telegram error in main menu: {e}")
    except Exception as e:
        logger.error(f"Error in main menu callback: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

@auth_router.message(Command("help"))
async def help_command(message: Message):
    """Show help information with comprehensive bot guide"""
    help_text = (
        "📚 <b>Справка по боту</b>\n\n"
        
        "🎯 <b>Основные функции:</b>\n"
        "• Управление компаниями и их данными\n"
        "• Добавление подразделений\n"
        "• Управление инструкторами (3 типа)\n"
        "• Генерация журналов инструктажей\n\n"
        
        "📋 <b>Типы документов:</b>\n"
        "• Журнал вводного инструктажа\n"
        "• Журнал инструктажа на рабочем месте\n"
        "• Журнал пожарного инструктажа\n\n"
        
        "⚙️ <b>Команды:</b>\n"
        "/start - Запуск бота\n"
        "/help - Эта справка\n"
        "/myid - Ваш Telegram ID\n\n"
        
        "🔧 <b>Как начать работу:</b>\n"
        "1. Получите токен у администратора\n"
        "2. Используйте /start для авторизации\n"
        "3. Добавьте компанию с данными\n"
        "4. Генерируйте документы\n\n"
        
        "❓ <b>Нужна помощь?</b>\n"
        "Обратитесь к администратору системы."
    )
    
    await message.answer(help_text, parse_mode="HTML")
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from states import AuthStates
from services.auth_service import AuthService
from utils.keyboards import get_start_keyboard
from config import ADMIN_ID

logger = logging.getLogger(__name__)
auth_router = Router()


@auth_router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    """Start command handler with simple auth flow."""
    await state.clear()
    user_id = message.from_user.id
    logger.info(f"/start from user {user_id} (@{message.from_user.username})")

    try:
        if AuthService.is_user_blacklisted(user_id):
            await message.answer(
                "🚫 <b>Доступ запрещён</b>\n\n"
                "Вы находитесь в черном списке. Если это ошибка — свяжитесь с администратором.",
                parse_mode="HTML",
            )
            return

        if AuthService.is_user_registered(user_id):
            await message.answer(
                "✅ <b>Вы уже авторизованы</b>\n\n"
                "Выберите нужное действие ниже:",
                reply_markup=get_start_keyboard(user_id, ADMIN_ID),
                parse_mode="HTML",
            )
        else:
            await message.answer(
                "👋 <b>Добро пожаловать!</b>\n\n"
                "Для начала работы введите токен доступа.",
                parse_mode="HTML",
            )
            await state.set_state(AuthStates.waiting_for_token)
    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        await message.answer(
            "⚠️ Произошла ошибка. Повторите попытку позже или обратитесь к администратору."
        )


@auth_router.message(AuthStates.waiting_for_token)
async def process_token(message: Message, state: FSMContext):
    """Token processing with validation and feedback."""
    token = message.text.strip() if message.text else ""
    user_id = message.from_user.id
    logger.info(f"Token validation attempt from user {user_id}")

    if not token:
        await message.answer("Пожалуйста, отправьте токен в ответ сообщением.")
        return

    if len(token) < 8:
        await message.answer("Токен слишком короткий. Проверьте и пришлите снова.")
        return

    try:
        if not AuthService.validate_token(token):
            await message.answer(
                "❌ <b>Неверный или уже использованный токен</b>\n\n"
                "Проверьте правильность токена и попробуйте ещё раз.",
                parse_mode="HTML",
            )
            return

        # Create or reactivate user, consume token
        ok, created_new = AuthService.create_user(user_id, message.from_user.username, message.from_user.first_name)
        AuthService.use_token(token, user_id)
        await state.clear()

        if created_new:
            from config import ADMIN_ID
            if ADMIN_ID and user_id == ADMIN_ID:
                AuthService.set_user_name(user_id, "Создатель")
                await message.answer(
                    "✅ Авторизация прошла успешно!\nИмя установлено: Создатель\n\nВыберите действие:",
                    reply_markup=get_start_keyboard(user_id, ADMIN_ID),
                )
            else:
                await message.answer("✅ Авторизация прошла успешно!\nКак к вам обращаться? Напишите ваше имя.")
                await state.set_state(AuthStates.waiting_for_name)
        else:
            await message.answer(
                "✅ Авторизация прошла успешно!\n\nВыберите действие:",
                reply_markup=get_start_keyboard(user_id, ADMIN_ID),
            )
    except Exception as e:
        logger.error(f"Error while processing token for {user_id}: {e}")
        await message.answer("⚠️ Не удалось обработать токен. Попробуйте позже.")


@auth_router.message(AuthStates.waiting_for_name)
async def process_name_after_token(message: Message, state: FSMContext):
    """Capture display name for newly authorized users."""
    name = (message.text or "").strip()
    if not name or len(name) < 2:
        await message.answer("Имя слишком короткое. Введите, пожалуйста, корректное имя.")
        return
    if len(name) > 100:
        await message.answer("Имя слишком длинное. Сократите до 100 символов.")
        return
    try:
        AuthService.set_user_name(message.from_user.id, name)
        await state.clear()
        await message.answer(
            f"Готово! Буду обращаться: {name}\n\nВыберите действие:",
            reply_markup=get_start_keyboard(message.from_user.id, ADMIN_ID),
        )
    except Exception as e:
        logger.error(f"Error saving display name: {e}")
        await message.answer("Не удалось сохранить имя. Попробуйте ещё раз.")


@auth_router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Return to main menu with user validation."""
    await callback.answer()
    await state.clear()
    user_id = callback.from_user.id

    try:
        if not AuthService.is_user_registered(user_id):
            await callback.message.edit_text(
                "ℹ️ <b>Вы не авторизованы</b>\n\nОтправьте /start, чтобы начать.",
                parse_mode="HTML",
            )
            return

        if AuthService.is_user_blacklisted(user_id):
            await callback.message.edit_text(
                "🚫 <b>Доступ запрещён</b>",
                parse_mode="HTML",
            )
            return

        await callback.message.edit_text(
            "🏠 <b>Главное меню</b>\n\nВыберите действие:",
            reply_markup=get_start_keyboard(user_id, ADMIN_ID),
            parse_mode="HTML",
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            logger.error(f"Telegram error in main menu: {e}")
    except Exception as e:
        logger.error(f"Error in main menu callback: {e}")
        await callback.answer("⚠️ Ошибка", show_alert=True)


@auth_router.message(Command("help"))
async def help_command(message: Message):
    """Show concise help information."""
    help_text = (
        "ℹ️ <b>Справка</b>\n\n"
        "Как работать с ботом:\n"
        "1) Получите токен у администратора\n"
        "2) Отправьте /start и введите токен\n"
        "3) Добавьте организацию и базовые данные\n"
        "4) Сформируйте нужные журналы\n\n"
        "/start — начать работу\n"
        "/help — справка\n"
        "/myid — показать ваш Telegram ID"
    )
    await message.answer(help_text, parse_mode="HTML")


@auth_router.message(Command("myid"))
async def myid_command(message: Message):
    user = message.from_user
    text = f"Ваш Telegram ID: <code>{user.id}</code>\n"
    if user.username:
        text += f"Username: @{user.username}\n"
    if user.first_name:
        text += f"Имя: {user.first_name}"
        if user.last_name:
            text += f" {user.last_name}"
    await message.answer(text, parse_mode="HTML")
