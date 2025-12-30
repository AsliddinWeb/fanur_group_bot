import base64
import time
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from config import PAYME_SECRET_KEY, PAYME_TEST_KEY, PAYME_AMOUNT, PAYME_TEST_MODE, PRIVATE_CHANNEL_ID
from services.payme_service import (
    get_order_by_id,
    get_order_by_payme_id,
    update_order_state,
    set_order_perform_time,
    set_order_cancel_time,
    get_orders_by_time_range
)

router = APIRouter()


# Payme error kodlari
class PaymeError:
    INVALID_AMOUNT = -31001
    ORDER_NOT_FOUND = -31050
    CANT_PERFORM = -31008
    TRANSACTION_NOT_FOUND = -31003
    INVALID_ACCOUNT = -31050
    METHOD_NOT_FOUND = -32601
    INVALID_AUTH = -32504


def error_response(code: int, message: str, data: str = None):
    """Xatolik javobi"""
    return {
        "error": {
            "code": code,
            "message": message,
            "data": data
        }
    }


def success_response(result: dict):
    """Muvaffaqiyatli javob"""
    return {"result": result}


def check_auth(request: Request) -> bool:
    """Payme autentifikatsiyasini tekshirish"""
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Basic "):
        return False

    try:
        encoded = auth_header.split(" ")[1]
        decoded = base64.b64decode(encoded).decode("utf-8")
        username, password = decoded.split(":")

        # Test yoki production key
        secret_key = PAYME_TEST_KEY if PAYME_TEST_MODE else PAYME_SECRET_KEY

        return password == secret_key
    except:
        return False


def timestamp_to_ms(dt) -> int:
    """Datetime ni millisekund ga aylantirish"""
    if dt is None:
        return 0
    if isinstance(dt, str):
        from datetime import datetime
        dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
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
    except:
        return JSONResponse(
            content=error_response(-32700, "Parse error"),
            status_code=200
        )

    method = data.get("method")
    params = data.get("params", {})

    # Usullarni yo'naltirish
    if method == "CheckPerformTransaction":
        result = await check_perform_transaction(params)
    elif method == "CreateTransaction":
        result = await create_transaction(params)
    elif method == "PerformTransaction":
        result = await perform_transaction(params)
    elif method == "CancelTransaction":
        result = await cancel_transaction(params)
    elif method == "CheckTransaction":
        result = await check_transaction(params)
    elif method == "GetStatement":
        result = await get_statement(params)
    else:
        result = error_response(PaymeError.METHOD_NOT_FOUND, "Method not found")

    return JSONResponse(content=result, status_code=200)


async def check_perform_transaction(params: dict):
    """To'lov qilish mumkinmi tekshirish"""
    account = params.get("account", {})
    amount = params.get("amount")
    user_id = account.get("user_id")

    # User ID tekshirish
    if not user_id:
        return error_response(PaymeError.INVALID_ACCOUNT, "User ID not found")

    # Summa tekshirish
    if amount != PAYME_AMOUNT:
        return error_response(
            PaymeError.INVALID_AMOUNT,
            f"Invalid amount. Expected {PAYME_AMOUNT}, got {amount}"
        )

    # Shu user uchun pending tranzaksiya bormi
    from services.payme_service import get_pending_order_by_user
    pending_order = await get_pending_order_by_user(int(user_id))
    if pending_order:
        return error_response(PaymeError.ORDER_NOT_FOUND, "Another transaction in progress")

    return success_response({"allow": True})


async def create_transaction(params: dict):
    """Tranzaksiya yaratish"""
    payme_id = params.get("id")
    account = params.get("account", {})
    amount = params.get("amount")
    time_param = params.get("time")
    user_id = account.get("user_id")

    # User ID tekshirish
    if not user_id:
        return error_response(PaymeError.INVALID_ACCOUNT, "User ID not found")

    # Summa tekshirish
    if amount != PAYME_AMOUNT:
        return error_response(PaymeError.INVALID_AMOUNT, "Invalid amount")

    # Mavjud tranzaksiya bormi (shu payme_id bilan)
    existing = await get_order_by_payme_id(payme_id)
    if existing:
        # Agar bekor qilingan bo'lsa
        if existing['state'] == -1:
            return error_response(PaymeError.CANT_PERFORM, "Transaction cancelled")

        return success_response({
            "create_time": timestamp_to_ms(existing['created_at']),
            "transaction": str(existing['id']),
            "state": existing['state']
        })

    # Shu user uchun pending tranzaksiya bormi
    from services.payme_service import get_pending_order_by_user
    pending_order = await get_pending_order_by_user(int(user_id))
    if pending_order:
        # Agar boshqa tranzaksiya band qilgan bo'lsa
        if pending_order['payme_transaction_id'] != payme_id:
            return error_response(PaymeError.ORDER_NOT_FOUND, "Another transaction in progress")

    # Yangi order yaratish
    from services.payme_service import create_order
    order_id = await create_order(int(user_id), amount)

    # Payme ID ni saqlash
    await update_order_state(order_id, 1, payme_id)

    order = await get_order_by_id(order_id)

    return success_response({
        "create_time": timestamp_to_ms(order['created_at']),
        "transaction": str(order['id']),
        "state": 1
    })


async def perform_transaction(params: dict):
    """To'lovni tasdiqlash"""
    payme_id = params.get("id")

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
    if order['state'] == -1:
        return error_response(PaymeError.CANT_PERFORM, "Transaction cancelled")

    # To'lovni tasdiqlash
    await set_order_perform_time(order['order_id'])

    # Foydalanuvchiga xabar yuborish
    await send_success_message(order['user_id'])

    order = await get_order_by_id(order['order_id'])

    return success_response({
        "transaction": str(order['id']),
        "perform_time": timestamp_to_ms(order['perform_time']),
        "state": 2
    })


async def cancel_transaction(params: dict):
    """Tranzaksiyani bekor qilish"""
    payme_id = params.get("id")
    reason = params.get("reason")

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

    order = await get_order_by_id(order['order_id'])

    return success_response({
        "transaction": str(order['id']),
        "cancel_time": timestamp_to_ms(order['cancel_time']),
        "state": order['state']
    })


async def check_transaction(params: dict):
    """Tranzaksiya holatini tekshirish"""
    payme_id = params.get("id")

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


async def get_statement(params: dict):
    """Hisobot olish"""
    from_time = params.get("from")
    to_time = params.get("to")

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

    return success_response({"transactions": transactions})


async def send_success_message(user_id: int):
    """Muvaffaqiyatli to'lov haqida xabar yuborish"""
    try:
        from main import get_bot
        bot_app = get_bot()

        if bot_app is None:
            print("Bot app not found")
            return

        # Bir martalik invite link yaratish
        try:
            invite = await bot_app.bot.create_chat_invite_link(
                chat_id=PRIVATE_CHANNEL_ID,
                member_limit=1
            )
            invite_link = invite.invite_link
        except Exception as e:
            print(f"Invite link yaratishda xato: {e}")
            invite_link = None

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

    except Exception as e:
        print(f"Xabar yuborishda xato: {e}")