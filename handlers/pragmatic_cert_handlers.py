import logging

from aiogram import Router, F
from aiogram.filters import StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiohttp import ConnectionTimeoutError
from redis import Redis

from config_data.config import Config
from filters.filters import (IsPragmaticCoursesFilter,
    CallBackFilter,
    IsCorrectData, IsValidProfileLink, IsPrivateChat)
from keyboards import (kb_back_cancel,
    kb_end_quiz,
    BUTT_GENDER)
from keyboards.keyboards import get_kb_courses, kb_butt_quiz
from keyboards.buttons import BUTT_COURSES
from lexicon import LexiconRu
from states.states import FSMPragmaticGetCert, FSMQuiz
from utils import get_username, StepikService, MessageProcessor

router = Router()
router.callback_query.filter(or_f(IsPragmaticCoursesFilter(),
                                  CallBackFilter('back'),
                                  StateFilter(FSMPragmaticGetCert)))
router.message.filter(IsPrivateChat())
logger = logging.getLogger(__name__)


@router.callback_query(IsPragmaticCoursesFilter())
async def get_pragmatic_certificates(
        clbk: CallbackQuery,
        state: FSMContext,
        config: Config,
        redis_data: Redis,
        msg_processor: MessageProcessor):
    logger.debug('Entry')

    tg_username = await get_username(clbk)
    stepik_service = StepikService(
        client_id=config.stepik.client_id,
        client_secret=config.stepik.client_secret,
        redis_client=redis_data,
        courses=config.courses_data.courses)
    logger.warning(
        f'Нажатие на курс {clbk.data}:{clbk.from_user.id}:{tg_username}')

    tg_id = str(clbk.from_user.id)
    course_id = clbk.data
    logger.info(
        f'Проверка наличия серт:TG_ID[{tg_id}]'
        f':{tg_username}:CourseID[{clbk.data}]')

    cert: str | bool = await stepik_service.check_cert_in_user(tg_id, course_id)
    logger.debug(f'{cert=}')

    if cert:
        value = await clbk.message.edit_text(
            'У вас есть сертификат этого курса 🤓\nВысылаем...📜☺️\n')
        try:
            path = await stepik_service.generate_certificate(
                state_data=state,
                type_update=clbk,
                w_text=config.w_text,
                exist_cert=True)

            await stepik_service.send_certificate(
                clbk=clbk,
                output_file=path,
                state=state,
                is_copy=True,
                course_id=course_id)

        except Exception as err:
            logger.debug(f'{err.__class__.__name__}', exc_info=True)

        await msg_processor.deletes_msg_a_delay(value, delay=5)
        await state.clear()
        logger.debug('Exit')
        return

    logger.info(f'Сертификат ID:{clbk.data} у TG_ID:{tg_id}'
                f':{tg_username} на руках не обнаружен')

    await state.update_data(course=clbk.data)
    logger.debug(f'Данные анкеты:{await state.get_data()}')

    value = await clbk.message.edit_text(
        LexiconRu.text_course_number_done,
        reply_markup=kb_back_cancel)

    await msg_processor.save_msg_id(value, msgs_for_del=True)
    await state.set_state(FSMPragmaticGetCert.fill_date_of_revocation)
    await clbk.answer()

    logger.info(f'State of {tg_username}:{await state.get_state()}')
    logger.debug('Exit')

@router.callback_query(F.data == 'back',
                       StateFilter(
                           FSMPragmaticGetCert.fill_date_of_revocation))
async def clbk_back_on_fill_course(clbk: CallbackQuery,
                                   state: FSMContext):
    logger.debug('Entry')

    await clbk.message.edit_text(LexiconRu.text_select_course,
                                 reply_markup=get_kb_courses())
    await state.set_state(FSMQuiz.fill_course)
    await clbk.answer()

    logger.debug('Exit')

@router.message(StateFilter(FSMPragmaticGetCert.fill_date_of_revocation),
                IsCorrectData())
async def msg_fill_date_revocation(msg: Message,
                                   state: FSMContext,
                                   date: str,
                                   msg_processor: MessageProcessor):
    logger.debug('Entry')

    await msg.delete()
    await msg_processor.deletes_messages(msgs_for_del=True)
    await state.update_data(date=date)

    logger.info(f'Дата {date} записана для TG_ID:{msg.from_user.id}'
                f':{await get_username(msg)}')

    value = await msg.answer(
        LexiconRu.text_data_done,
        reply_markup=kb_back_cancel,
        disable_web_page_preview=True)
    await msg_processor.save_msg_id(value, msgs_for_del=True)
    await state.set_state(FSMPragmaticGetCert.fill_link_to_stepik_profile)

    logger.debug('Exit')


@router.callback_query(F.data == 'back',
                       StateFilter(
                           FSMPragmaticGetCert.fill_link_to_stepik_profile))
async def clbk_back_to_fill_date_revocation(clbk: CallbackQuery,
                                            state: FSMContext):
    logger.debug('Entry')

    await clbk.message.edit_text(LexiconRu.text_course_number_done,
                                 reply_markup=kb_back_cancel)
    await state.set_state(FSMPragmaticGetCert.fill_date_of_revocation)
    await clbk.answer()

    logger.debug('Exit')


@router.message(StateFilter(FSMPragmaticGetCert.fill_link_to_stepik_profile),
                IsValidProfileLink())
async def msg_sent_stepik_link(
        msg: Message,
        state: FSMContext,
        stepik_user_id: str,
        msg_processor: MessageProcessor):

    logger.debug('Entry')
    logger.info(f'Записана ссылка {msg.text} от TG_ID:{msg.from_user.id}'
                f':{await get_username(msg)}')

    await state.update_data(stepik_user_id=stepik_user_id)
    await msg_processor.deletes_messages(msgs_for_del=True)

    text = (f'{'Имя:':<7}{await state.get_value('full_name')}\n'
            f'{'Пол:':<7}{BUTT_GENDER[await state.get_value('gender')]}\n'
            f'{'Курс:':<7}{BUTT_COURSES[await state.get_value('course')]}\n'
            f'Stepik_ID:   {await state.get_value('stepik_user_id')}\n'
            f'Дата отзыва: {await state.get_value('date')}')

    await state.set_state(FSMPragmaticGetCert.data_confirm)
    await msg.delete()
    await msg.answer('Нажмите подтвердить, если все данные верны.\n\n'
                     f'<code>{text}</code>', reply_markup=kb_end_quiz)
    logger.debug('Exit')

@router.callback_query(F.data == 'back',
                       StateFilter(FSMPragmaticGetCert.data_confirm))
async def clbk_back_to_sent_stepik_link(clbk: CallbackQuery,
                                        state: FSMContext):
    logger.debug('Entry')

    await clbk.message.edit_text(LexiconRu.text_data_done,
                                 reply_markup=kb_back_cancel)
    await state.set_state(FSMPragmaticGetCert.fill_link_to_stepik_profile)
    await clbk.answer()

    logger.debug('Exit')


@router.callback_query(F.data == 'done',
                       StateFilter(FSMPragmaticGetCert.data_confirm))
async def clbk_done(
        clbk: CallbackQuery,
        state: FSMContext,
        redis_data: Redis,
        config: Config,
        msg_processor: MessageProcessor):
    logger.debug('Entry')

    stepik_service = StepikService(
        client_id=config.stepik.client_id,
        client_secret=config.stepik.client_secret,
        redis_client=redis_data,
        courses=config.courses_data.courses)
    logger.info(
        f'Анкета проверяется:{clbk.from_user.id}'
        f':{await get_username(clbk)}')
    value1 = await clbk.message.edit_text(
        'Ваши данные проверяются⌛\n'
        'Ожидайте выдачи сертификата📜\n')

    stepik_user_id = await state.get_value('stepik_user_id')
    tg_username = await get_username(clbk)

    # Проверяем, есть ли у пользователя уже сохраненный Stepik ID
    existing_stepik_id = await redis_data.hget(
        name=str(clbk.from_user.id),
        key='stepik_user_id')
    if existing_stepik_id:
        if existing_stepik_id != stepik_user_id:
            await clbk.message.edit_text(
                'Вы пытаетесь использовать другой Stepik-аккаунт. '
                'Если вы ошиблись - повторите или обратитесь к администратору.')
            logger.warning(
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
                other_user_stepik_id = await redis_data.hget(
                    user_key,
                    'stepik_user_id')
                if other_user_stepik_id == stepik_user_id:
                    await clbk.message.edit_text(
                        'Этот Stepik-аккаунт уже используется другим пользователем. '
                        'Обратитесь к администратору.')
                    logger.warning(
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
            stepik_user_id,
            course_id,
            access_token)
    except ConnectionTimeoutError as e:
        logger.error(
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
            logger.error(f'{err=}', exc_info=True)
            value = await clbk.message.answer(
                'Произошла не предвиденная ошибка,'
                ' обратитесь к администратору.')
            await msg_processor.save_msg_id(value, msgs_for_del=True)
            await state.clear()
            await msg_processor.deletes_msg_a_delay(value1, delay=5)
            logger.debug('Exit:error')
            return

        try:
            await clbk.answer('Идет проверка…')
            # генерация сертификата
            logger.info(
                f'Генерация сертификата для'
                f' :{clbk.from_user.id}:{tg_username}')
            path = await stepik_service.generate_certificate(
                state,
                type_update=clbk,
                w_text=config.w_text)

        except Exception as err:
            logger.error(f'{err=}', exc_info=True)
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
            logger.error(f'{err=}', exc_info=True)
        finally:
            await state.clear()
            await clbk.answer()
    else:
        logger.info(
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
        await msg_processor.deletes_msg_a_delay(value, delay=10, indication=True)
        value = await clbk.message.answer(
            LexiconRu.text_survey,
            reply_markup=kb_butt_quiz,
            disable_web_page_preview=True)
        await msg_processor.deletes_msg_a_delay(value1, delay=5)
        await msg_processor.save_msg_id(value, msgs_for_del=True)
        await state.clear()
        await clbk.answer()
    logger.debug(f'Exit')











