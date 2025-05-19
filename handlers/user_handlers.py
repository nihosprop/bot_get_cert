import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message
from redis import Redis

from config_data.config import Stepik
from filters.filters import (IsCorrectData, IsFullName, IsValidProfileLink)
from keyboards import (BUTT_COURSES,
                       BUTT_GENDER,
                       kb_back_cancel,
                       kb_butt_cancel,
                       kb_courses,
                       kb_create_promo,
                       kb_end_quiz,
                       kb_select_gender)
from lexicon.lexicon_ru import LexiconRu, Links
from keyboards.keyboards import kb_butt_quiz
from states.states import FSMQuiz
from utils import (StepikService,
                   check_user_in_group,
                   get_username,
                   shifts_the_date_forward)
from utils.utils import MessageProcessor

user_router = Router()
logger = logging.getLogger()
logger_user_hand = logging.getLogger(__name__)

@user_router.message(F.text.lower().find('спасибо') == 0)
async def msg_thanks(msg: Message, msg_processor: MessageProcessor):
    logger_user_hand.debug('Entry')
    logger_user_hand.info(f'Сказал Спасибо!:{await get_username(msg)}')
    await msg.delete()
    answer_thnks = await msg.answer(f'{await get_username(msg)}!'
                                    f' Спасибо Вам за приятные слова!\n'
                                    'Мы это ценим!😇')
    await msg_processor.deletes_msg_a_delay(answer_thnks,
                                            delay=15,
                                            indication=True)
    logger_user_hand.debug('Exit')

@user_router.message(F.text == '/start')
async def cmd_start(
        msg: Message, state: FSMContext, msg_processor: MessageProcessor):
    logger_user_hand.info(f'cmd_start:{msg.from_user.id}'
                          f':{await get_username(msg)}')
    await msg_processor.deletes_messages(msgs_for_del=True)
    await state.clear()
    value = await msg.answer(LexiconRu.text_survey, reply_markup=kb_butt_quiz,
                             disable_web_page_preview=True)
    await msg_processor.save_msg_id(value, msgs_for_del=True)


@user_router.callback_query(F.data == 'get_promo')
async def temp(clbk: CallbackQuery):
    await clbk.message.edit_text('Выберите курс, по которому хотите получить'
                                 ' скидку👇', reply_markup=kb_create_promo)
    await clbk.answer()


@user_router.callback_query(F.data == '/cancel', StateFilter(default_state))
async def clbk_cancel(clbk: CallbackQuery, state: FSMContext):
    logger_user_hand.info(f'cancel_default_state:{clbk.from_user.id}'
                          f':{await get_username(clbk)}')
    msg_processor = MessageProcessor(clbk, state)
    try:
        await state.clear()
    except Exception as err:
        logger_user_hand.error(f'{err=}', exc_info=True)
    value = await clbk.message.edit_text(LexiconRu.text_survey,
                                         reply_markup=kb_butt_quiz,
                                         disable_web_page_preview=True)
    await msg_processor.save_msg_id(value, msgs_for_del=True)
    await clbk.answer()


@user_router.callback_query(F.data == 'back',
                            StateFilter(FSMQuiz.fill_date_of_revocation))
async def clbk_back_fill_date(clbk: CallbackQuery, state: FSMContext):
    logger_user_hand.debug('Entry')
    logger_user_hand.info(f'[fill_date -> fill_courses]:{clbk.from_user.id}'
                          f':{await get_username(clbk)}')
    try:
        await clbk.message.edit_text(LexiconRu.text_select_course,
                                     reply_markup=kb_courses)
        await state.set_state(FSMQuiz.fill_course)
        await clbk.answer()
    except Exception as err:
        logger_user_hand.error(f'{err=}')
    logger_user_hand.debug('Exit')


@user_router.callback_query(F.data == 'back', StateFilter(FSMQuiz.fill_course))
async def clbk_back_fill_course(clbk: CallbackQuery, state: FSMContext):
    logger_user_hand.info(f'[fill_courses -> fill_gender]:{clbk.from_user.id}'
                          f':{await get_username(clbk)}')
    await clbk.message.edit_text(LexiconRu.text_gender,
                                 reply_markup=kb_select_gender)
    await state.set_state(FSMQuiz.fill_gender)
    await clbk.answer()


@user_router.callback_query(F.data == 'back', StateFilter(FSMQuiz.fill_gender))
async def clbk_back_fill_(
        clbk: CallbackQuery, state: FSMContext, msg_processor: MessageProcessor):
    logger_user_hand.info(f'[fill_gender -> fill_full_name]:{clbk.from_user.id}'
                          f':{await get_username(clbk)}')
    value = await clbk.message.edit_text(LexiconRu.text_sent_fullname,
                                         reply_markup=kb_butt_cancel)
    await msg_processor.save_msg_id(value, msgs_for_del=True)
    await state.set_state(FSMQuiz.fill_full_name)
    await clbk.answer()


@user_router.callback_query(F.data == 'back',
                            StateFilter(FSMQuiz.fill_link_cert))
async def clbk_back_fill_link_cert(
        clbk: CallbackQuery, state: FSMContext, msg_processor: MessageProcessor):
    logger_user_hand.debug('Entry')
    logger_user_hand.info(f'[fill_link_cert -> fill_date]:{clbk.from_user.id}'
                          f':{await get_username(clbk)}')
    value = await clbk.message.edit_text(LexiconRu.text_course_number_done,
                                         reply_markup=kb_back_cancel)
    await msg_processor.save_msg_id(value, msgs_for_del=True)
    await state.set_state(FSMQuiz.fill_date_of_revocation)
    await clbk.answer()
    logger_user_hand.debug('Exit')


@user_router.callback_query(F.data == 'back', StateFilter(FSMQuiz.end))
async def clbk_back_end(
        clbk: CallbackQuery, state: FSMContext, msg_processor: MessageProcessor):
    logger_user_hand.debug('Entry')
    logger_user_hand.info(f'[end -> fill_link_cert]:{clbk.from_user.id}'
                          f':{await get_username(clbk)}')
    try:
        await msg_processor.deletes_messages(msgs_for_del=True)
    except Exception as err:
        logger_user_hand.error(f'{err.__class__.__name__=}', exc_info=True)
    value = await clbk.message.edit_text(LexiconRu.text_data_done,
                                         reply_markup=kb_back_cancel)
    await msg_processor.save_msg_id(value, msgs_for_del=True)
    await state.set_state(FSMQuiz.fill_link_cert)
    await clbk.answer()
    logger_user_hand.debug('Exit')


@user_router.message(StateFilter(default_state), ~F.text.in_({'/start'}),
                     F.content_type.in_(
                             {"text", "sticker", "photo", "video", "document"}))
async def msg_other(msg: Message, msg_processor: MessageProcessor):
    if msg.text == '/admin':
        await msg.delete()
        value = await msg.answer('Эта команда для администраторов 😉')
        logger_user_hand.warning(f'Тапнул админку:'
                                 f'{msg.from_user.id}:'
                                 f'{await get_username(msg)}')
        await msg_processor.deletes_msg_a_delay(value, delay=4, indication=True)
        return

    await msg.delete()
    value = await msg.answer(f'{await get_username(msg)}, используйте '
                             f'пожалуйста кнопки для взаимодействия с ботом🙂')
    logger_user_hand.warning(f'Работа с кнопками:Сообщение от->'
                             f'{msg.from_user.id}:'
                             f'{await get_username(msg)}:'
                             f'{msg.content_type}:{msg.text}')
    await msg_processor.deletes_msg_a_delay(value, delay=5, indication=True)


@user_router.callback_query(F.data == '/cancel', ~StateFilter(default_state))
async def clbk_cancel_in_state(
        clbk: CallbackQuery, state: FSMContext, msg_processor: MessageProcessor):
    logger_user_hand.info(f'cancel_in_state:{clbk.from_user.id}'
                          f':{await get_username(clbk)}')
    logger_user_hand.debug(f'Entry {clbk_cancel_in_state.__name__=}')
    try:
        await state.clear()
    except Exception as err:
        logger_user_hand.error(f'{err=}')

    value = await clbk.message.edit_text(LexiconRu.text_survey,
                                         reply_markup=kb_butt_quiz,
                                         disable_web_page_preview=True)
    await msg_processor.save_msg_id(value, msgs_for_del=True)
    await clbk.answer()
    logger_user_hand.debug(f'Exit')


@user_router.callback_query(F.data == 'get_cert', StateFilter(default_state))
async def clbk_get_cert(
        clbk: CallbackQuery, state: FSMContext, msg_processor: MessageProcessor):
    logger_user_hand.info(f'Запрос сертификата:{clbk.from_user.id}'
                          f':{await get_username(clbk)}')
    if not await check_user_in_group(clbk):
        logger_user_hand.info(f'Отсутствие в группе:{clbk.from_user.id}'
                              f':{await get_username(clbk)}')
        await clbk.answer('Вы еще не вступили в нашу дружную группу'
                          ' Лучший по Python ☺️', show_alert=True)
        return

    value = await clbk.message.edit_text(LexiconRu.text_sent_fullname,
                                         reply_markup=kb_butt_cancel)
    await msg_processor.save_msg_id(value, msgs_for_del=True)
    await state.set_state(FSMQuiz.fill_full_name)
    await clbk.answer()


@user_router.callback_query(F.data.in_(BUTT_GENDER),
                            StateFilter(FSMQuiz.fill_gender))
async def clbk_gender(clbk: CallbackQuery, state: FSMContext):
    logger_user_hand.info(f'Выбран пол:{clbk.from_user.id}'
                          f':{await get_username(clbk)}:{clbk.data}')
    await state.update_data(gender=clbk.data)
    await clbk.message.edit_text(LexiconRu.text_select_course,
                                 reply_markup=kb_courses)
    await state.set_state(FSMQuiz.fill_course)
    await clbk.answer()


@user_router.callback_query(F.data.in_([name for name in BUTT_COURSES if
        name.startswith(('id_1', 'id_2', 'id_3'))]),
        StateFilter(FSMQuiz.fill_course))
async def clbk_select_course(
        clbk: CallbackQuery, state: FSMContext, stepik: Stepik,
        redis_data: Redis, w_text: bool, msg_processor: MessageProcessor):
    stepik_service = StepikService(stepik.client_id, stepik.client_secret,
                                   redis_data)
    course_id = str(clbk.data).split('_')[-1]
    logger_user_hand.info(f'Проверка наличия серт:{clbk.from_user.id}'
                          f':{await get_username(clbk)}:{clbk.data}')
    cert = await stepik_service.check_cert_in_user(str(clbk.from_user.id),
                                                   course_id)
    logger_user_hand.debug(f'{cert=}')
    if cert:
        value = await clbk.message.edit_text('У вас есть сертификат этого '
                                             'курса 🤓\nВысылаем 📜☺️\n')
        try:
            path = await stepik_service.generate_certificate(state, clbk,
                                                             w_text=w_text,
                                                             exist_cert=True)
            # отправка сертификата
            await stepik_service.send_certificate(clbk, path, state,
                                                  is_copy=True,
                                                  course_id=course_id)
        except Exception as err:
            logger_user_hand.debug(f'{err.__class__.__name__=}', exc_info=True)

        await msg_processor.deletes_msg_a_delay(value, delay=5)
        await state.clear()

        # msg_promo_id = await redis_data.get(f'{clbk.from_user.id}_msg_promo_id')
        # logger_user_hand.debug(f'Взятие id промо мсг для '
        #                        f'удаления {msg_promo_id=}')
        # try:
        #     if msg_promo_id:
        #         await clbk.bot.delete_message(chat_id=str(clbk.message.chat.id),
        #                                       message_id=msg_promo_id)
        # except TelegramBadRequest as err:
        #     logger_user_hand.error(f'{err=}')
        # try:
        #     msg_promo = await msg_processor.send_message_with_delay(
        #             clbk.message.chat.id, text=LexiconRu.text_promo.format(
        #                     end_date=await shifts_the_date_forward()), delay=15,
        #             preview_link=Links.link_questions_to_ivan)
            # запись и логирование id промо месаги для удаления
            # logger_user_hand.debug(
            #         f'Запись id_промо_мсг:{clbk.from_user.id}_msg_promo_id')
            # await redis_data.set(f'{clbk.from_user.id}_msg_promo_id',
            #                      str(msg_promo.message_id))
        # except Exception as err:
        #     logger_user_hand.error(f'{err.__class__.__name__=}', exc_info=True)
        logger_user_hand.debug(f'Exit')
        return
    logger_user_hand.info(f'Серт на руках не обнаружен:{clbk.from_user.id}'
                          f':{await get_username(clbk)}:{clbk.data}')
    await state.update_data(course=clbk.data)
    value = await clbk.message.edit_text(LexiconRu.text_course_number_done,
                                         reply_markup=kb_back_cancel)
    await msg_processor.save_msg_id(value, msgs_for_del=True)
    await state.set_state(FSMQuiz.fill_date_of_revocation)
    await clbk.answer()


@user_router.callback_query(F.data.in_([name for name in BUTT_COURSES if
                                        name.startswith(('id_4', 'id_5',
                                        'id_6'))]),
                            StateFilter(FSMQuiz.fill_course))
async def clbk_select_empty_course(clbk: CallbackQuery):
    await clbk.answer('Курс находиться в разработке', show_alert=True)
    logger_user_hand.warning(f'Нажатие на курс {clbk.data}:{clbk.from_user.id}:'
                             f'{await get_username(clbk)}')


@user_router.message(
        StateFilter(FSMQuiz.fill_gender, FSMQuiz.fill_course, FSMQuiz.end),
        F.content_type.in_({"text", "sticker", "photo", "video", "document"}))
async def delete_unexpected_messages(
        msg: Message, msg_processor: MessageProcessor):
    """
    Удаляет сообщения пользователя, если он отправляет текст/медиа, вместо
    нажатия на кнопку.
    """
    logger_user_hand.warning(f"Перехвачено сообщение:{msg.content_type}:"
                             f"{msg.text}:"
                             f"{msg.from_user.id}:{await get_username(msg)}")
    await msg.delete()
    reminder = await msg.answer(
            f'{await get_username(msg)} пожалуйста, используйте кнопки для '
            f'взаимодействия с ботом🙃')
    await msg_processor.deletes_msg_a_delay(reminder, delay=5, indication=True)


@user_router.message(StateFilter(FSMQuiz.fill_full_name), IsFullName())
async def msg_full_name(
        msg: Message, state: FSMContext, full_name,
        msg_processor: MessageProcessor):
    logger_user_hand.info(f'Корректное ФИО:{msg.from_user.id}'
                          f':{await get_username(msg)}')
    await msg.delete()
    logger_user_hand.debug(f'{await state.get_state()=}')
    await state.update_data(full_name=full_name)
    logger_user_hand.debug(f'{await state.get_data()=}')
    await msg_processor.deletes_messages(msgs_for_del=True)
    await msg.answer(LexiconRu.text_gender, reply_markup=kb_select_gender)
    await state.set_state(FSMQuiz.fill_gender)


@user_router.message(StateFilter(FSMQuiz.fill_date_of_revocation),
                     IsCorrectData())
async def msg_sent_date(
        msg: Message, state: FSMContext, date: str,
        msg_processor: MessageProcessor):
    logger_user_hand.debug('Entry')

    await msg.delete()
    await msg_processor.deletes_messages(msgs_for_del=True)
    await state.update_data(date=date)
    logger_user_hand.info(f'Дата записана:{msg.from_user.id}'
                          f':{await get_username(msg)}:[{date}]')
    value = await msg.answer(LexiconRu.text_data_done,
                             reply_markup=kb_back_cancel,
                             disable_web_page_preview=True)
    await msg_processor.save_msg_id(value, msgs_for_del=True)
    await state.set_state(FSMQuiz.fill_link_cert)

    logger_user_hand.debug('Exit')


@user_router.callback_query(F.data == 'done', StateFilter(FSMQuiz.end))
async def clbk_done(
        clbk: CallbackQuery, state: FSMContext, redis_data: Redis,
        stepik: Stepik, w_text: bool, msg_processor: MessageProcessor):
    logger_user_hand.debug('Entry')
    stepik_service = StepikService(stepik.client_id, stepik.client_secret,
                                   redis_data)
    logger_user_hand.info(f'Анкета проверяется:{clbk.from_user.id}'
                          f':{await get_username(clbk)}')
    value1 = await clbk.message.edit_text('Ваши данные проверяются⌛\n'
                                          'Ожидайте выдачи сертификата📜\n')

    stepik_user_id = await state.get_value('stepik_user_id')
    course_id = str(await state.get_value('course')).split('_')[-1]
    access_token = await stepik_service.get_stepik_access_token()
    certificates = await stepik_service.check_cert_in_stepik(stepik_user_id,
                                                             course_id,
                                                             access_token)
    if certificates == 'PRIVATE':
        value = await clbk.message.edit_text(f'{await get_username(clbk)},'
                                             f'{LexiconRu.text_privacy_instructions}')
        await state.clear()
        await msg_processor.save_msg_id(value, msgs_for_del=True)
        await clbk.answer()
        return

    if certificates:
        try:
            number = await redis_data.incr('end_number')
            number_str = str(number).zfill(6)
            await state.update_data(end_number=number_str)
            await redis_data.set('end_number', number)
        except Exception as err:
            logger_user_hand.error(f'{err=}', exc_info=True)
            value = await clbk.message.answer('Произошла не предвиденная ошибка,'
                                              ' обратитесь к администратору.')
            await msg_processor.save_msg_id(value, msgs_for_del=True)
            await state.clear()
            logger_user_hand.debug('Exit:error')
            return

        try:
            await clbk.answer('Идет проверка…')
            # генерация сертификата
            logger_user_hand.info(f'Генерация сертификата для'
                                  f' :{clbk.from_user.id}'
                                  f':{await get_username(clbk)}')
            path = await stepik_service.generate_certificate(state,
                                                             type_update=clbk,
                                                             w_text=w_text)
        except Exception as err:
            logger_user_hand.error(f'{err=}', exc_info=True)
            value = await clbk.message.answer('Произошла ошибка😯\nПопробуйте '
                                              'позже или обратитесь к'
                                              ' администратору🤖')
            await msg_processor.deletes_msg_a_delay(value, 20, indication=True)
            await state.clear()
            return

        try:
            # отправка сертификата
            await stepik_service.send_certificate(clbk, path, state,
                                                  course_id=course_id)
            await msg_processor.deletes_msg_a_delay(value=value1, delay=1)

            # временное отключение promo месаги

            # взятие id_promo сообщения для удаления
            # msg_promo_id = await redis_data.get(
            #         f'{clbk.from_user.id}_msg_promo_id')
            # logger_user_hand.debug(f'Серт не в наличии, id промо мсг для '
            #                        f'удаления {msg_promo_id=}')
            # if msg_promo_id:
            #     logger_user_hand.debug(f'Удаляем {msg_promo_id=}')
            #     await clbk.bot.delete_message(str(clbk.message.chat.id),
            #                                   msg_promo_id)
            # msg_promo = await msg_processor.send_message_with_delay(
            #         clbk.message.chat.id, text=LexiconRu.text_promo.format(
            #                 end_date=await shifts_the_date_forward()), delay=15,
            #         preview_link=Links.link_questions_to_ivan)

            # запись id промо месаги для удаления
            # await redis_data.set(f'{clbk.from_user.id}_msg_promo_id',
            #                      str(msg_promo.message_id))
            # logger_user_hand.debug(f'Запись id промо мсг для удаления '
            #                        f'{msg_promo.message_id=}')

        except Exception as err:
            logger_user_hand.error(f'{err=}', exc_info=True)
        finally:
            await state.clear()
            await clbk.answer()
    else:
        logger_user_hand.info(f'Отсутствует серт на Stepik'
                              f':{clbk.from_user.id}'
                              f':{await get_username(clbk)}')
        value = await clbk.message.answer(f'{await get_username(clbk)}, у вас '
                                          f'пока нет сертификата этого курса🙁')
        await msg_processor.deletes_msg_a_delay(value, delay=10, indication=True)
        value = await clbk.message.answer(LexiconRu.text_survey,
                                          reply_markup=kb_butt_quiz,
                                          disable_web_page_preview=True)
        await msg_processor.deletes_msg_a_delay(value1, delay=5, indication=True)
        await msg_processor.save_msg_id(value, msgs_for_del=True)
        await state.clear()
        await clbk.answer()
    logger_user_hand.debug(f'Exit')


@user_router.message(StateFilter(FSMQuiz.fill_link_cert), IsValidProfileLink())
async def msg_sent_stepik_link(
        msg: Message, state: FSMContext, stepik_user_id: str,
        msg_processor: MessageProcessor):
    logger_user_hand.info(f'Ссылка записана:{msg.from_user.id}'
                          f':{await get_username(msg)}:[{msg.text}]')
    # запись Stepik_user_id
    await state.update_data(stepik_user_id=stepik_user_id)
    await msg_processor.deletes_messages(msgs_for_del=True)

    text = (f'{'Имя:':<7}{await state.get_value('full_name')}\n'
            f'{'Пол:':<7}{BUTT_GENDER[await state.get_value('gender')]}\n'
            f'{'Курс:':<7}{BUTT_COURSES[await state.get_value('course')]}\n'
            f'Stepik_ID:   {await state.get_value('stepik_user_id')}\n'
            f'Дата отзыва: {await state.get_value('date')}')
    await state.set_state(FSMQuiz.end)
    await msg.delete()
    await msg.answer('Нажмите подтвердить, если все данные верны.\n\n'
                     f'<code>{text}</code>', reply_markup=kb_end_quiz)
