from pyrogram import Client, filters
from pyrogram.types import *
import config

app = Client(
    "storagebot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

user_files = {}
broadcast_mode = False


# ================= MENU =================

def main_menu(user_id):

    if user_id == config.ADMIN_ID:

        return ReplyKeyboardMarkup(
            [
                ["📤 Upload", "🔗 Create Link"],
                ["📂 My Files", "👤 Account"],
                ["📢 Broadcast"]
            ],
            resize_keyboard=True
        )

    else:

        return ReplyKeyboardMarkup(
            [
                ["📤 Upload", "🔗 Create Link"],
                ["📂 My Files", "👤 Account"]
            ],
            resize_keyboard=True
        )


# ================= FORCE JOIN =================

async def check_join(client, user_id):

    try:
        member = await client.get_chat_member(
            config.FORCE_GROUP,
            user_id
        )

        if member.status in ["member", "administrator", "creator"]:
            return True

    except:
        pass

    return False


# ================= START =================

@app.on_message(filters.command("start"))
async def start(client, message):

    user_id = message.from_user.id

    joined = await check_join(client, user_id)

    if not joined:

        return await message.reply(
            "⚠️ Join group dulu",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Join Group", url=config.GROUP_LINK)],
                    [InlineKeyboardButton("Verifikasi", callback_data="checkjoin")]
                ]
            )
        )

    await message.reply(
        "📦 Storage Bot\n\nGunakan menu di bawah.",
        reply_markup=main_menu(user_id)
    )


# ================= VERIFY =================

@app.on_callback_query(filters.regex("checkjoin"))
async def verify(client, query):

    joined = await check_join(client, query.from_user.id)

    if not joined:

        return await query.answer(
            "Kamu belum join group",
            show_alert=True
        )

    await query.message.edit(
        "✅ Verifikasi berhasil\nSilakan gunakan bot."
    )


# ================= UPLOAD MENU =================

@app.on_message(filters.regex("📤 Upload"))
async def upload_menu(client, message):

    await message.reply(
        "📤 Kirim video atau file ke bot.\n\n"
        "File akan otomatis tersimpan di storage."
    )


# ================= HANDLE FILE =================

@app.on_message(filters.private & (filters.video | filters.document))
async def upload_file(client, message):

    user_id = message.from_user.id

    status = await message.reply("📤 Upload ke storage...")

    sent = await message.copy(config.STORAGE_CHANNEL)

    if user_id not in user_files:
        user_files[user_id] = []

    user_files[user_id].append(sent.id)

    await status.edit("✅ File berhasil disimpan")


# ================= CREATE LINK =================

@app.on_message(filters.regex("🔗 Create Link"))
async def create_link(client, message):

    user_id = message.from_user.id

    if user_id not in user_files:

        return await message.reply(
            "❌ Kamu belum upload file"
        )

    first_id = user_files[user_id][0]

    me = await client.get_me()

    link = f"https://t.me/{me.username}?start={first_id}"

    await message.reply(
        f"🔗 Link kamu:\n\n{link}"
    )


# ================= MY FILES =================

@app.on_message(filters.regex("📂 My Files"))
async def myfiles(client, message):

    user_id = message.from_user.id

    if user_id not in user_files:

        return await message.reply(
            "📂 Kamu belum punya file"
        )

    files = user_files[user_id][:10]

    for fid in files:

        try:
            await client.copy_message(
                message.chat.id,
                config.STORAGE_CHANNEL,
                fid
            )
        except:
            pass


# ================= ACCOUNT =================

@app.on_message(filters.regex("👤 Account"))
async def account(client, message):

    user_id = message.from_user.id

    total = 0

    if user_id in user_files:
        total = len(user_files[user_id])

    await message.reply(
        f"👤 ID: `{user_id}`\n"
        f"📂 Total file: {total}"
    )


# ================= BROADCAST =================

@app.on_message(filters.regex("📢 Broadcast") & filters.user(config.ADMIN_ID))
async def broadcast_start(client, message):

    global broadcast_mode

    broadcast_mode = True

    await message.reply(
        "📢 Kirim pesan broadcast sekarang"
    )


@app.on_message(filters.text & filters.user(config.ADMIN_ID))
async def broadcast_send(client, message):

    global broadcast_mode

    if not broadcast_mode:
        return

    total = 0

    for uid in user_files:

        try:

            await client.send_message(uid, message.text)

            total += 1

        except:
            pass

    broadcast_mode = False

    await message.reply(
        f"✅ Broadcast terkirim ke {total} user"
    )


print("Bot running...")

app.run()
