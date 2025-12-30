import base64
import logging
from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from config import (
    PAYME_SECRET_KEY,
    PAYME_TEST_KEY,
    PAYME_AMOUNT,
    PAYME_TEST_MODE,
    PRIVATE_CHANNEL_ID
)
from services.payme_service import (
    create_order,
    get_order_by_id,
    get_order_by_payme_id,
    get_pending_order_by_user,
    update_order_state,
    set_order_perform_time,
    set_order_cancel_time,
    get_orders_by_time_range,
    has_successful_payment
)
from services.user_service import get_user

# Logger
logger = logging.getLogger(__name__)

router = APIRouter()


# Payme error kodlari
class PaymeError:
    INVALID_AMOUNT = -31001
    ORDER_NOT_FOUND = -31050
    USER_NOT_FOUND = -31050
    ALREADY_PAID = -31051
    CANT_PERFORM = -31008
    TRANSACTION_NOT_FOUND = -31003
    INVALID_ACCOUNT = -31050
    METHOD_NOT_FOUND = -32601
    INVALID_AUTH = -32504
    PARSE_ERROR = -32700


def error_response(code: int, message: str, data: str = None) -> dict:
    """Xatolik javobi"""
    response = {
        "error": {
            "code": code,
            "message": message,
            "data": data
        }
    }
    logger.warning(f"Payme error: {code} - {message}")
    return response


def success_response(result: dict) -> dict:
    """Muvaffaqiyatli javob"""
    return {"result": result}


def check_auth(request: Request) -> bool:
    """Payme autentifikatsiyasini tekshirish"""
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Basic "):
        logger.warning("Invalid auth header format")
        return False

    try:
        encoded = auth_header.split(" ")[1]
        decoded = base64.b64decode(encoded).decode("utf-8")
        username, password = decoded.split(":")

        # Test yoki production key
        secret_key = PAYME_TEST_KEY if PAYME_TEST_MODE else PAYME_SECRET_KEY

        if password == secret_key:
            return True

        logger.warning(f"Invalid secret key from {username}")
        return False
    except Exception as e:
        logger.error(f"Auth error: {e}")
        return False


def timestamp_to_ms(dt) -> int:
    """Datetime ni millisekund ga aylantirish"""
    if dt is None:
        return 0
    if isinstance(dt, str):
        try:
            dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return 0
    return int(dt.timestamp() * 1000)


@router.post("/payme")
async def payme_webhook(request: Request):
    """Payme webhook handler"""

    # Autentifikatsiya
    if not check_auth(request):
        return JSONResponse(
            content=error_response(PaymeError.INVALID_AUTH, "Invalid authorization"),
            status_code=200
        )

    # JSON body
    try:
        data = await request.json()
        logger.info(f"Payme request: {data.get('method')}")
    except Exception as e:
        logger.error(f"JSON parse error: {e}")
        return JSONResponse(
            content=error_response(PaymeError.PARSE_ERROR, "Parse error"),
            status_code=200
        )

    method = data.get("method")
    params = data.get("params", {})

    # Usullarni yo'naltirish
    methods = {
        "CheckPerformTransaction": check_perform_transaction,
        "CreateTransaction": create_transaction,
        "PerformTransaction": perform_transaction,
        "CancelTransaction": cancel_transaction,
        "CheckTransaction": check_transaction,
        "GetStatement": get_statement
    }

    handler = methods.get(method)
    if handler:
        result = await handler(params)
    else:
        result = error_response(PaymeError.METHOD_NOT_FOUND, f"Method '{method}' not found")

    return JSONResponse(content=result, status_code=200)


async def check_perform_transaction(params: dict) -> dict:
    """To'lov qilish mumkinmi tekshirish"""
    account = params.get("account", {})
    amount = params.get("amount")
    user_id = account.get("user_id")

    logger.info(f"CheckPerformTransaction: user_id={user_id}, amount={amount}")

    # User ID tekshirish
    if not user_id:
        return error_response(PaymeError.INVALID_ACCOUNT, "User ID not found")

    # User ID raqammi tekshirish
    try:
        user_id_int = int(user_id)
    except ValueError:
        return error_response(PaymeError.INVALID_ACCOUNT, "Invalid user ID format")

    # User bazada bormi tekshirish
    user = await get_user(user_id_int)
    if not user:
        return error_response(PaymeError.USER_NOT_FOUND, "User not found")

    # Summa tekshirish
    if amount != PAYME_AMOUNT:
        return error_response(
            PaymeError.INVALID_AMOUNT,
            f"Invalid amount. Expected {PAYME_AMOUNT}, got {amount}"
        )

    # User allaqachon to'lov qilganmi
    if await has_successful_payment(user_id_int):
        return error_response(PaymeError.ALREADY_PAID, "User already paid")

    # Shu user uchun pending tranzaksiya bormi
    try:
        pending_order = await get_pending_order_by_user(user_id_int)
        if pending_order:
            return error_response(PaymeError.ORDER_NOT_FOUND, "Another transaction in progress")
    except Exception as e:
        logger.error(f"Check pending order error: {e}")

    return success_response({"allow": True})


async def create_transaction(params: dict) -> dict:
    """Tranzaksiya yaratish"""
    payme_id = params.get("id")
    account = params.get("account", {})
    amount = params.get("amount")
    time_param = params.get("time")
    user_id = account.get("user_id")

    logger.info(f"CreateTransaction: user_id={user_id}, payme_id={payme_id}, amount={amount}")

    # User ID tekshirish
    if not user_id:
        return error_response(PaymeError.INVALID_ACCOUNT, "User ID not found")

    # User ID raqammi tekshirish
    try:
        user_id_int = int(user_id)
    except ValueError:
        return error_response(PaymeError.INVALID_ACCOUNT, "Invalid user ID format")

    # User bazada bormi tekshirish
    user = await get_user(user_id_int)
    if not user:
        return error_response(PaymeError.USER_NOT_FOUND, "User not found")

    # Summa tekshirish
    if amount != PAYME_AMOUNT:
        return error_response(PaymeError.INVALID_AMOUNT, "Invalid amount")

    # User allaqachon to'lov qilganmi
    if await has_successful_payment(user_id_int):
        return error_response(PaymeError.ALREADY_PAID, "User already paid")

    try:
        # Mavjud tranzaksiya bormi (shu payme_id bilan)
        existing = await get_order_by_payme_id(payme_id)
        if existing:
            # Agar bekor qilingan bo'lsa
            if existing['state'] in [-1, -2]:
                return error_response(PaymeError.CANT_PERFORM, "Transaction cancelled")

            return success_response({
                "create_time": timestamp_to_ms(existing['created_at']),
                "transaction": str(existing['id']),
                "state": existing['state']
            })

        # Shu user uchun pending tranzaksiya bormi
        pending_order = await get_pending_order_by_user(user_id_int)
        if pending_order:
            # Agar boshqa tranzaksiya band qilgan bo'lsa
            if pending_order['payme_transaction_id'] != payme_id:
                return error_response(PaymeError.ORDER_NOT_FOUND, "Another transaction in progress")

        # Yangi order yaratish
        order_id = await create_order(user_id_int, amount)
        logger.info(f"Order created: {order_id}")

        # Payme ID ni saqlash
        await update_order_state(order_id, 1, payme_id)

        order = await get_order_by_id(order_id)

        return success_response({
            "create_time": timestamp_to_ms(order['created_at']),
            "transaction": str(order['id']),
            "state": 1
        })

    except Exception as e:
        logger.error(f"CreateTransaction error: {e}")
        return error_response(PaymeError.CANT_PERFORM, "Internal error")


async def perform_transaction(params: dict) -> dict:
    """To'lovni tasdiqlash"""
    payme_id = params.get("id")

    logger.info(f"PerformTransaction: payme_id={payme_id}")

    try:
        # Tranzaksiyani topish
        order = await get_order_by_payme_id(payme_id)
        if not order:
            return error_response(PaymeError.TRANSACTION_NOT_FOUND, "Transaction not found")

        # Allaqachon bajarilgan
        if order['state'] == 2:
            return success_response({
                "transaction": str(order['id']),
                "perform_time": timestamp_to_ms(order['perform_time']),
                "state": 2
            })

        # Bekor qilingan
        if order['state'] in [-1, -2]:
            return error_response(PaymeError.CANT_PERFORM, "Transaction cancelled")

        # To'lovni tasdiqlash
        await set_order_perform_time(order['order_id'])
        logger.info(f"Payment confirmed for user: {order['user_id']}")

        # Foydalanuvchiga xabar yuborish
        await send_success_message(order['user_id'])

        order = await get_order_by_id(order['order_id'])

        return success_response({
            "transaction": str(order['id']),
            "perform_time": timestamp_to_ms(order['perform_time']),
            "state": 2
        })

    except Exception as e:
        logger.error(f"PerformTransaction error: {e}")
        return error_response(PaymeError.CANT_PERFORM, "Internal error")


async def cancel_transaction(params: dict) -> dict:
    """Tranzaksiyani bekor qilish"""
    payme_id = params.get("id")
    reason = params.get("reason")

    logger.info(f"CancelTransaction: payme_id={payme_id}, reason={reason}")

    try:
        # Tranzaksiyani topish
        order = await get_order_by_payme_id(payme_id)
        if not order:
            return error_response(PaymeError.TRANSACTION_NOT_FOUND, "Transaction not found")

        # Allaqachon bekor qilingan
        if order['state'] in [-1, -2]:
            return success_response({
                "transaction": str(order['id']),
                "cancel_time": timestamp_to_ms(order['cancel_time']),
                "state": order['state']
            })

        # State bo'yicha bekor qilish
        # state=1 (yaratilgan) -> -1
        # state=2 (bajarilgan) -> -2
        new_state = -1 if order['state'] == 1 else -2

        await set_order_cancel_time(order['order_id'], reason, new_state)
        logger.info(f"Transaction cancelled: {payme_id}, new_state={new_state}")

        order = await get_order_by_id(order['order_id'])

        return success_response({
            "transaction": str(order['id']),
            "cancel_time": timestamp_to_ms(order['cancel_time']),
            "state": order['state']
        })

    except Exception as e:
        logger.error(f"CancelTransaction error: {e}")
        return error_response(PaymeError.CANT_PERFORM, "Internal error")


async def check_transaction(params: dict) -> dict:
    """Tranzaksiya holatini tekshirish"""
    payme_id = params.get("id")

    logger.info(f"CheckTransaction: payme_id={payme_id}")

    try:
        # Tranzaksiyani topish
        order = await get_order_by_payme_id(payme_id)
        if not order:
            return error_response(PaymeError.TRANSACTION_NOT_FOUND, "Transaction not found")

        return success_response({
            "create_time": timestamp_to_ms(order['created_at']),
            "perform_time": timestamp_to_ms(order['perform_time']),
            "cancel_time": timestamp_to_ms(order['cancel_time']),
            "transaction": str(order['id']),
            "state": order['state'],
            "reason": order['reason']
        })

    except Exception as e:
        logger.error(f"CheckTransaction error: {e}")
        return error_response(PaymeError.TRANSACTION_NOT_FOUND, "Internal error")


async def get_statement(params: dict) -> dict:
    """Hisobot olish"""
    from_time = params.get("from")
    to_time = params.get("to")

    logger.info(f"GetStatement: from={from_time}, to={to_time}")

    try:
        orders = await get_orders_by_time_range(from_time, to_time)

        transactions = []
        for order in orders:
            transactions.append({
                "id": order['payme_transaction_id'],
                "time": timestamp_to_ms(order['created_at']),
                "amount": order['amount'],
                "account": {
                    "user_id": str(order['user_id'])
                },
                "create_time": timestamp_to_ms(order['created_at']),
                "perform_time": timestamp_to_ms(order['perform_time']),
                "cancel_time": timestamp_to_ms(order['cancel_time']),
                "transaction": str(order['id']),
                "state": order['state'],
                "reason": order['reason']
            })

        logger.info(f"GetStatement: found {len(transactions)} transactions")
        return success_response({"transactions": transactions})

    except Exception as e:
        logger.error(f"GetStatement error: {e}")
        return success_response({"transactions": []})


async def send_success_message(user_id: int):
    """Muvaffaqiyatli to'lov haqida xabar yuborish"""
    try:
        from main import get_bot
        bot_app = get_bot()

        if bot_app is None:
            logger.error("Bot app not found")
            return

        # Bir martalik invite link yaratish
        invite_link = None
        try:
            invite = await bot_app.bot.create_chat_invite_link(
                chat_id=PRIVATE_CHANNEL_ID,
                member_limit=1
            )
            invite_link = invite.invite_link
            logger.info(f"Invite link created for user: {user_id}")
        except Exception as e:
            logger.error(f"Invite link yaratishda xato: {e}")

        # Xabar yuborish
        if invite_link:
            text = (
                "🎉 <b>Tabriklaymiz!</b>\n\n"
                "Sizning to'lovingiz muvaffaqiyatli qabul qilindi!\n\n"
                f"🔗 Yopiq kanalga kirish uchun link:\n{invite_link}\n\n"
                "⚠️ Link faqat bir martalik!"
            )
        else:
            text = (
                "🎉 <b>Tabriklaymiz!</b>\n\n"
                "Sizning to'lovingiz muvaffaqiyatli qabul qilindi!\n\n"
                "⚠️ Admin siz bilan tez orada bog'lanadi."
            )

        await bot_app.bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode='HTML'
        )
        logger.info(f"Success message sent to user: {user_id}")

    except Exception as e:
        logger.error(f"Xabar yuborishda xato: {e}")