import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message
from aiohttp import ConnectionTimeoutError
from redis import Redis

from config_data.config import Config
from filters.filters import (IsCorrectData,
    IsFullName,
    IsValidProfileLink,
    IsPrivateChat, IsBestPythonCoursesFilter, IsAdmins)
from keyboards import (BUTT_COURSES,
    BUTT_GENDER,
    kb_back_cancel,
    kb_butt_cancel,
    kb_create_promo,
    kb_end_quiz,
    kb_select_gender)
from keyboards.keyboards import get_kb_courses
from lexicon.lexicon_ru import LexiconRu
from keyboards.keyboards import kb_butt_quiz
from states.states import FSMQuiz
from utils import (StepikService,
    check_user_in_group,
    get_username)
from utils.utils import MessageProcessor

user_router = Router()
user_router.message.filter(IsPrivateChat())
logger_user_hand = logging.getLogger(__name__)

@user_router.message(F.text.lower().find('спасибо') == 0)
async def msg_thanks(msg: Message, msg_processor: MessageProcessor):
    logger_user_hand.debug('Entry')
    logger_user_hand.info(f'Сказал Спасибо!:{await get_username(msg)}')
    await msg.delete()
    answer_thnks = await msg.answer(
        f'{await get_username(msg)}!'
        f' Спасибо Вам за приятные слова!\n'
        f'Мы это ценим!😇')

    await msg_processor.deletes_msg_a_delay(
        answer_thnks,
        delay=15,
        indication=True)
    logger_user_hand.debug('Exit')


@user_router.message(F.text == '/start')
# @user_router.message(CommandStart())
async def cmd_start(
        msg: Message,
        state: FSMContext,
        msg_processor: MessageProcessor):

    logger_user_hand.info(
        f'cmd_start:{msg.from_user.id}:{await get_username(msg)}')

    # logger_user_hand.debug(
    #     msg.model_dump_json(
    #         indent=4,
    #         exclude_none=True))
    # logger_user_hand.debug(f'{msg.text}')

    await msg_processor.deletes_messages(msgs_for_del=True, msgs_remove_kb=True)
    await state.clear()
    value = await msg.answer(
        LexiconRu.text_survey, reply_markup=kb_butt_quiz,
        disable_web_page_preview=True)
    await msg_processor.save_msg_id(value, msgs_for_del=True)


@user_router.callback_query(F.data == 'get_promo')
async def temp(clbk: CallbackQuery):
    await clbk.message.edit_text(
        'Выберите курс, по которому хотите получить'
        ' скидку👇', reply_markup=kb_create_promo)
    await clbk.answer()


@user_router.callback_query(F.data == '/cancel', StateFilter(default_state))
async def clbk_cancel(clbk: CallbackQuery, state: FSMContext):
    logger_user_hand.info(
        f'cancel_default_state:{clbk.from_user.id}'
        f':{await get_username(clbk)}')
    msg_processor = MessageProcessor(clbk, state)
    try:
        await state.clear()
    except Exception as err:
        logger_user_hand.error(f'{err=}', exc_info=True)
    value = await clbk.message.edit_text(
        LexiconRu.text_survey,
        reply_markup=kb_butt_quiz,
        disable_web_page_preview=True)
    await msg_processor.save_msg_id(value, msgs_for_del=True)
    await clbk.answer()


@user_router.callback_query(
    F.data == 'back',
    StateFilter(FSMQuiz.fill_date_of_revocation))
async def clbk_back_fill_date(clbk: CallbackQuery, state: FSMContext):
    logger_user_hand.debug('Entry')
    logger_user_hand.info(
        f'[fill_date -> fill_courses]:{clbk.from_user.id}'
        f':{await get_username(clbk)}')
    try:
        await clbk.message.edit_text(
            LexiconRu.text_select_course,
            reply_markup=get_kb_courses())
        await state.set_state(FSMQuiz.fill_course)
        await clbk.answer()
    except Exception as err:
        logger_user_hand.error(f'{err=}')
    logger_user_hand.debug('Exit')


@user_router.callback_query(F.data == 'back', StateFilter(FSMQuiz.fill_course))
async def clbk_back_fill_course(clbk: CallbackQuery, state: FSMContext):
    logger_user_hand.info(
        f'[fill_courses -> fill_gender]:{clbk.from_user.id}'
        f':{await get_username(clbk)}')
    await clbk.message.edit_text(
        LexiconRu.text_gender,
        reply_markup=kb_select_gender)
    await state.set_state(FSMQuiz.fill_gender)
    await clbk.answer()


@user_router.callback_query(F.data == 'back', StateFilter(FSMQuiz.fill_gender))
async def clbk_back_fill_(
        clbk: CallbackQuery, state: FSMContext, msg_processor: MessageProcessor):
    logger_user_hand.info(
        f'[fill_gender -> fill_full_name]:{clbk.from_user.id}'
        f':{await get_username(clbk)}')
    value = await clbk.message.edit_text(
        LexiconRu.text_sent_fullname,
        reply_markup=kb_butt_cancel)
    await msg_processor.save_msg_id(value, msgs_for_del=True)
    await state.set_state(FSMQuiz.fill_full_name)
    await clbk.answer()


@user_router.callback_query(
    F.data == 'back',
    StateFilter(FSMQuiz.fill_link_to_stepik_profile))
async def clbk_back_fill_link_cert(
        clbk: CallbackQuery, state: FSMContext, msg_processor: MessageProcessor):
    logger_user_hand.debug('Entry')
    logger_user_hand.info(
        f'[fill_link_cert -> fill_date]:{clbk.from_user.id}'
        f':{await get_username(clbk)}')
    value = await clbk.message.edit_text(
        LexiconRu.text_course_number_done,
        reply_markup=kb_back_cancel)
    await msg_processor.save_msg_id(value, msgs_for_del=True)
    await state.set_state(FSMQuiz.fill_date_of_revocation)
    await clbk.answer()
    logger_user_hand.debug('Exit')


@user_router.callback_query(F.data == 'back', StateFilter(FSMQuiz.data_confirm))
async def clbk_back_end(
        clbk: CallbackQuery, state: FSMContext, msg_processor: MessageProcessor):
    logger_user_hand.debug('Entry')
    logger_user_hand.info(
        f'[end -> fill_link_cert]:{clbk.from_user.id}'
        f':{await get_username(clbk)}')
    try:
        await msg_processor.deletes_messages(msgs_for_del=True)
    except Exception as err:
        logger_user_hand.error(f'{err.__class__.__name__=}', exc_info=True)
    value = await clbk.message.edit_text(
        LexiconRu.text_data_done,
        reply_markup=kb_back_cancel)
    await msg_processor.save_msg_id(value, msgs_for_del=True)
    await state.set_state(FSMQuiz.fill_link_to_stepik_profile)
    await clbk.answer()
    logger_user_hand.debug('Exit')


@user_router.message(
    StateFilter(default_state),
    ~IsAdmins(),
    ~F.text.in_({'/start'},),
    F.content_type.in_(
        {"text", "sticker", "photo", "video", "document"}))
async def msg_other(msg: Message, msg_processor: MessageProcessor):
    if msg.text == '/admin':
        await msg.delete()
        value = await msg.answer('Эта команда для администраторов 😉')
        logger_user_hand.warning(
            f'Тапнул админку:'
            f'{msg.from_user.id}:'
            f'{await get_username(msg)}')
        await msg_processor.deletes_msg_a_delay(value, delay=4, indication=True)
        return

    await msg.delete()
    value = await msg.answer(
        f'{await get_username(msg)}, используйте '
        f'пожалуйста кнопки для взаимодействия с ботом🙂')
    logger_user_hand.warning(
        f'Работа с кнопками:Сообщение от->'
        f'{msg.from_user.id}:'
        f'{await get_username(msg)}:'
        f'{msg.content_type}:{msg.text}')
    await msg_processor.deletes_msg_a_delay(value, delay=5, indication=True)


@user_router.callback_query(F.data == '/cancel', ~StateFilter(default_state))
async def clbk_cancel_in_state(
        clbk: CallbackQuery, state: FSMContext, msg_processor: MessageProcessor):
    logger_user_hand.info(
        f'cancel_in_state:{clbk.from_user.id}'
        f':{await get_username(clbk)}')
    logger_user_hand.debug(f'Entry {clbk_cancel_in_state.__name__=}')
    try:
        await state.clear()
    except Exception as err:
        logger_user_hand.error(f'{err=}')

    value = await clbk.message.edit_text(
        LexiconRu.text_survey,
        reply_markup=kb_butt_quiz,
        disable_web_page_preview=True)
    await msg_processor.save_msg_id(value, msgs_for_del=True)
    await clbk.answer()
    logger_user_hand.debug(f'Exit')


@user_router.callback_query(F.data == 'get_cert', StateFilter(default_state))
async def clbk_get_cert(
        clbk: CallbackQuery,
        state: FSMContext,
        msg_processor: MessageProcessor,
        config: Config):
    logger_user_hand.info(
        f'Запрос сертификата:{clbk.from_user.id}'
        f':{await get_username(clbk)}')
    if not await check_user_in_group(clbk,
                                     tg_target_channel=config.tg_target_channel):
        logger_user_hand.info(
            f'Юзер {clbk.from_user.id}:{await get_username(clbk)} отсутствует '
            f'в паблике {config.tg_target_channel}')
        await clbk.answer(
            'Вы еще не подписались на наш крутой паблик'
            ' Лучший по Python ☺️', show_alert=True)
        return

    value = await clbk.message.edit_text(
        LexiconRu.text_sent_fullname,
        reply_markup=kb_butt_cancel)
    await msg_processor.save_msg_id(value, msgs_for_del=True)
    await state.set_state(FSMQuiz.fill_full_name)
    await clbk.answer()


@user_router.callback_query(
    F.data.in_(BUTT_GENDER),
    StateFilter(FSMQuiz.fill_gender))
async def clbk_gender(clbk: CallbackQuery, state: FSMContext):
    logger_user_hand.info(
        f'Выбран пол:{clbk.from_user.id}'
        f':{await get_username(clbk)}:{clbk.data}')
    logger_user_hand.debug(f'{await state.get_state()=}')
    await state.update_data(gender=clbk.data)
    await clbk.message.edit_text(
        LexiconRu.text_select_course,
        reply_markup=get_kb_courses())
    await state.set_state(FSMQuiz.fill_course)
    await clbk.answer()



@user_router.callback_query(IsBestPythonCoursesFilter(),
                            StateFilter(FSMQuiz.fill_course))
async def clbk_select_course(
        clbk: CallbackQuery,
        state: FSMContext,
        config: Config,
        redis_data: Redis,
        msg_processor: MessageProcessor):
    stepik_service = StepikService(
        client_secret=config.stepik.client_secret,
        client_id=config.stepik.client_id,
        redis_client=redis_data,
        courses=config.courses_data.courses)
    tg_id = str(clbk.from_user.id)
    course_id = clbk.data
    logger_user_hand.info(
        f'Проверка наличия серт:{tg_id}'
        f':{await get_username(clbk)}:{clbk.data}')

    cert: str | bool = await stepik_service.check_cert_in_user(tg_id, course_id)
    if cert:
        value = await clbk.message.edit_text(
            'У вас есть сертификат этого '
            'курса 🤓\nВысылаем... 📜☺️\n')
        try:
            path = await stepik_service.generate_certificate(
                state,
                clbk,
                w_text=config.w_text,
                exist_cert=True)
            # отправка сертификата
            await stepik_service.send_certificate(
                clbk,
                path,
                state,
                is_copy=True,
                course_id=course_id)
        except Exception as err:
            logger_user_hand.debug(
                f'{err.__class__.__name__=}',
                exc_info=True)

        await msg_processor.deletes_msg_a_delay(value, delay=5)
        await state.clear()
        logger_user_hand.debug(f'Exit')
        return
    course_name = stepik_service.courses.get(int(clbk.data)).name
    logger_user_hand.info(
        f'Сертификат курса {course_name}:{clbk.data} у TG_ID:{tg_id}:'
        f':{await get_username(clbk)} на руках не обнаружен')

    await state.update_data(course=clbk.data)
    value = await clbk.message.edit_text(
        LexiconRu.text_course_number_done,
        reply_markup=kb_back_cancel)
    await msg_processor.save_msg_id(value, msgs_for_del=True)
    await state.set_state(FSMQuiz.fill_date_of_revocation)
    await clbk.answer()


@user_router.message(
    StateFilter(FSMQuiz.fill_gender, FSMQuiz.fill_course, FSMQuiz.data_confirm),
    F.content_type.in_({"text", "sticker", "photo", "video", "document"}))
async def delete_unexpected_messages(
        msg: Message, msg_processor: MessageProcessor):
    """
    Удаляет сообщения пользователя, если он отправляет текст/медиа, вместо
    нажатия на кнопку.
    """
    logger_user_hand.warning(
        f"Перехвачено сообщение:{msg.content_type}:"
        f"[{msg.text}]:"
        f"TG_ID[{msg.from_user.id}]"
        f":{await get_username(msg)}")
    await msg.delete()
    reminder = await msg.answer(
        f'{await get_username(msg)}, используйте пожалуйста кнопки для '
        f'взаимодействия с ботом🙃')
    await msg_processor.deletes_msg_a_delay(reminder, delay=5, indication=True)


@user_router.message(StateFilter(FSMQuiz.fill_full_name), IsFullName())
async def msg_full_name(
        msg: Message, state: FSMContext, full_name,
        msg_processor: MessageProcessor):
    logger_user_hand.info(
        f'Корректное ФИО:{msg.from_user.id}'
        f':{await get_username(msg)}:{full_name}')
    await msg.delete()
    logger_user_hand.debug(f'{await state.get_state()=}')
    await state.update_data(full_name=full_name)
    logger_user_hand.debug(f'{await state.get_data()=}')
    await msg_processor.deletes_messages(msgs_for_del=True)
    await msg.answer(LexiconRu.text_gender, reply_markup=kb_select_gender)
    await state.set_state(FSMQuiz.fill_gender)


@user_router.message(
    StateFilter(FSMQuiz.fill_date_of_revocation),
    IsCorrectData())
async def msg_sent_date(
        msg: Message, state: FSMContext, date: str,
        msg_processor: MessageProcessor):
    logger_user_hand.debug('Entry')

    await msg.delete()
    await msg_processor.deletes_messages(msgs_for_del=True)
    await state.update_data(date=date)
    logger_user_hand.info(
        f'Дата записана:{msg.from_user.id}'
        f':{await get_username(msg)}:[{date}]')
    value = await msg.answer(
        LexiconRu.text_data_done,
        reply_markup=kb_back_cancel,
        disable_web_page_preview=True)
    await msg_processor.save_msg_id(value, msgs_for_del=True)
    await state.set_state(FSMQuiz.fill_link_to_stepik_profile)

    logger_user_hand.debug('Exit')


@user_router.callback_query(F.data == 'done', StateFilter(FSMQuiz.data_confirm))
async def clbk_done(
        clbk: CallbackQuery,
        state: FSMContext,
        redis_data: Redis,
        config: Config,
        msg_processor: MessageProcessor):
    """
    Handles the final confirmation step of the quiz.

    This handler processes the user's quiz data, verifies the Stepik account,
    checks for existing certificates, and generates a new certificate if all
    conditions are met.

    Args:
        clbk (CallbackQuery): The callback query object from the user's action.
        state (FSMContext): The state of the finite state machine.
        redis_data (Redis): The Redis client for data storage.
        config (Config): The application's configuration object.
        msg_processor (MessageProcessor): The message processor for handling messages.
    """
    logger_user_hand.debug('Entry')

    stepik_service = StepikService(
        client_id=config.stepik.client_id,
        client_secret=config.stepik.client_secret,
        redis_client=redis_data,
        courses=config.courses_data.courses)
    logger_user_hand.info(
        f'Анкета проверяется:{clbk.from_user.id}'
        f':{await get_username(clbk)}')
    value1 = await clbk.message.edit_text(
        'Ваши данные проверяются⌛\n'
        'Ожидайте выдачи сертификата📜\n')

    stepik_user_id = await state.get_value('stepik_user_id')
    tg_username = await get_username(clbk)

    # Проверяем, есть ли у пользователя уже сохраненный Stepik ID
    existing_stepik_id = await redis_data.hget(name=str(clbk.from_user.id),
                                               key='stepik_user_id')
    if existing_stepik_id:
        if existing_stepik_id != stepik_user_id:
            await clbk.message.edit_text(
                'Вы пытаетесь использовать другой Stepik-аккаунт. '
                'Если вы ошиблись - повторите или обратитесь к администратору.')
            logger_user_hand.warning(
                f'Попытка смены Stepik ID для '
                f'TG_ID:{clbk.from_user.id}:{tg_username}. '
                f'Привязанный SEPIK_ID:{existing_stepik_id}, Новый SEPIK_ID:'
                f'{stepik_user_id}')
            await state.clear()
            await clbk.answer()
            return
    else:
        # Проверяем, не занят ли этот Stepik ID другим пользователем
        all_user_hashes = await redis_data.keys('*')
        for user_key in all_user_hashes:
            if user_key.isdigit() and user_key != str(clbk.from_user.id):
                other_user_stepik_id = await redis_data.hget(user_key,
                                                             'stepik_user_id')
                if other_user_stepik_id == stepik_user_id:
                    await clbk.message.edit_text(
                        'Этот Stepik-аккаунт уже используется другим пользователем. '
                        'Обратитесь к администратору.')
                    logger_user_hand.warning(
                        f'Попытка TG_ID:{clbk.from_user.id}:'
                        f'{tg_username} использовать '
                        f'занятый STEPIK ID:{stepik_user_id}')
                    await state.clear()
                    await clbk.answer()
                    return
        
        # Если все проверки пройдены, сохраняем Stepik ID
        await redis_data.hset(
            name=str(clbk.from_user.id),
            key='stepik_user_id',
            value=stepik_user_id)

    course_clbk_data = await state.get_value('course')
    course_id = (course_clbk_data.split('_')[-1]
                 if '_' in course_clbk_data else course_clbk_data)

    try:
        access_token = await stepik_service.get_stepik_access_token()
        certificates = await stepik_service.check_cert_in_stepik(
            stepik_user_id=stepik_user_id,
            course_id=course_id,
            access_token=access_token,
            tg_username=tg_username,
            config=config)
    except ConnectionTimeoutError as e:
        logger_user_hand.error(
            f'Не удалось проверить сертификат на Stepik для'
            f' TG_ID:{clbk.from_user.id}:{tg_username},'
            f' STEPIK_USER_ID:{stepik_user_id},'
            f' COURSE_ID:{course_id}, '
            f'из-за ошибки передачи данных! Сертификат выдан без проверки!, {e}')
        certificates = True

    if certificates == 'PRIVATE':
        value = await clbk.message.edit_text(
            f'{tg_username},'
            f'{LexiconRu.text_privacy_instructions}')
        await state.clear()
        await msg_processor.save_msg_id(value, msgs_for_del=True)
        await clbk.answer()
        return

    if certificates:
        try:
            if int(course_id) in config.courses_data.best_in_python_courses:
                number = await redis_data.incr('end_number')
            else:
                number = await redis_data.incr(f'end_number_{course_id}')

            number_str = str(number).zfill(6)
            await state.update_data(end_number=number_str)

        except Exception as err:
            logger_user_hand.error(f'{err=}', exc_info=True)
            value = await clbk.message.answer(
                'Произошла не предвиденная ошибка,'
                ' обратитесь к администратору.')
            await msg_processor.save_msg_id(value, msgs_for_del=True)
            await state.clear()
            await msg_processor.deletes_msg_a_delay(value1, delay=5)
            logger_user_hand.debug('Exit:error')
            return

        try:
            await clbk.answer('Идет проверка…')
            # генерация сертификата
            logger_user_hand.info(
                f'Генерация сертификата для'
                f':{clbk.from_user.id}:{tg_username}')
            path = await stepik_service.generate_certificate(
                state,
                type_update=clbk,
                w_text=config.w_text)

        except Exception as err:
            logger_user_hand.error(f'{err=}', exc_info=True)
            value = await clbk.message.answer(
                'Произошла ошибка😯\nПопробуйте '
                'позже или обратитесь к администратору🤖')
            await msg_processor.deletes_msg_a_delay(value=value1, delay=2)
            await msg_processor.deletes_msg_a_delay(value, 20, indication=True)
            await state.clear()
            return

        try:
            # отправка сертификата
            await stepik_service.send_certificate(
                clbk=clbk,
                output_file=path,
                state=state,
                course_id=course_id)
            await msg_processor.deletes_msg_a_delay(value=value1, delay=1)

        except Exception as err:
            logger_user_hand.error(f'{err=}', exc_info=True)
        finally:
            await state.clear()
            await clbk.answer()
    else:
        logger_user_hand.info(
            f'Отсутствует серт на Stepik'
            f':{clbk.from_user.id}:{tg_username}')
        value = await clbk.message.answer(
            f'{tg_username}, у вас '
            f'пока нет сертификата этого курса '
            f'на Stepik🙁\n'
            f'Наберите нужное для сертификата '
            f'количество баллов, получите '
            f'сертификат на платформе и приходите '
            f'снова, за экземпляром от команды '
            f'курса😉')
        await msg_processor.deletes_msg_a_delay(value, delay=15, indication=True)
        value = await clbk.message.answer(
            LexiconRu.text_survey,
            reply_markup=kb_butt_quiz,
            disable_web_page_preview=True)
        await msg_processor.deletes_msg_a_delay(value1, delay=5)
        await msg_processor.save_msg_id(value, msgs_for_del=True)
        await state.clear()
        await clbk.answer()
    logger_user_hand.debug(f'Exit')


@user_router.message(
    StateFilter(FSMQuiz.fill_link_to_stepik_profile),
    IsValidProfileLink())
async def msg_sent_stepik_link(
        msg: Message, state: FSMContext, stepik_user_id: str,
        msg_processor: MessageProcessor):
    logger_user_hand.info(
        f'Ссылка записана:{msg.from_user.id}'
        f':{await get_username(msg)}:[{msg.text}]')
    # запись Stepik_user_id
    await state.update_data(stepik_user_id=stepik_user_id)
    await msg_processor.deletes_messages(msgs_for_del=True)

    text = (f'{'Имя:':<7}{await state.get_value('full_name')}\n'
            f'{'Пол:':<7}{BUTT_GENDER[await state.get_value('gender')]}\n'
            f'{'Курс:':<7}{BUTT_COURSES[await state.get_value('course')]}\n'
            f'Stepik_ID:   {await state.get_value('stepik_user_id')}\n'
            f'Дата отзыва: {await state.get_value('date')}')
    await state.set_state(FSMQuiz.data_confirm)
    await msg.delete()
    await msg.answer(
        'Нажмите подтвердить, если все данные верны.\n\n'
        f'<code>{text}</code>', reply_markup=kb_end_quiz)
