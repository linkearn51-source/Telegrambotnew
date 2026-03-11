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
user_create = {}

# ================= MENU =================

def menu(uid):

    if uid == config.ADMIN_ID:

        return ReplyKeyboardMarkup(
            [
                ["📤 Upload", "🔗 Create"],
                ["📂 MyFiles", "👤 Account"],
                ["🔔 Group", "📢 Broadcast"]
            ],
            resize_keyboard=True
        )

    else:

        return ReplyKeyboardMarkup(
            [
                ["📤 Upload", "🔗 Create"],
                ["📂 MyFiles", "👤 Account"],
                ["🔔 Group"]
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

        if member.status not in ["left", "kicked"]:
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
            "⚠️ Kamu harus join group dulu",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("👥 Join Group", url=config.GROUP_LINK)],
                    [InlineKeyboardButton("✅ Verifikasi", callback_data="checkjoin")]
                ]
            )
        )

    args = message.text.split()

    # jika buka link create
    if len(args) > 1:

        code = args[1]

        if code in user_create:

            files = user_create[code]

            for fid in files:

                try:
                    await client.copy_message(
                        message.chat.id,
                        config.STORAGE_CHANNEL,
                        fid
                    )
                except:
                    pass

            return

    await message.reply(
        "📦 Storage Bot\nGunakan menu di bawah.",
        reply_markup=menu(user_id)
    )


# ================= VERIFY =================

@app.on_callback_query(filters.regex("checkjoin"))
async def verify(client, query):

    joined = await check_join(client, query.from_user.id)

    if not joined:

        return await query.answer(
            "❌ Kamu belum join group",
            show_alert=True
        )

    await query.message.edit(
        "✅ Verifikasi berhasil\nSekarang bot bisa digunakan"
    )


# ================= UPLOAD =================

@app.on_message(filters.regex("📤 Upload"))
async def upload_info(client, message):

    await message.reply(
        "📤 Kirim video atau file ke bot.\n"
        "File akan otomatis disimpan di storage."
    )


@app.on_message(filters.private & (filters.video | filters.document))
async def upload_file(client, message):

    user_id = message.from_user.id

    size = message.document.file_size if message.document else message.video.file_size

    size_mb = round(size / 1024 / 1024, 2)

    status = await message.reply("📤 Upload ke storage...")

    sent = await message.copy(config.STORAGE_CHANNEL)

    if user_id not in user_files:
        user_files[user_id] = []

    user_files[user_id].append(sent.id)

    total = len(user_files[user_id])

    await status.edit(
        f"✅ File tersimpan\n\n"
        f"📦 Size: {size_mb} MB\n"
        f"📂 Total file kamu: {total}"
    )


# ================= MY FILES =================

@app.on_message(filters.regex("📂 MyFiles"))
async def myfiles(client, message):

    user_id = message.from_user.id

    if user_id not in user_files:

        return await message.reply(
            "📂 Kamu belum upload file"
        )

    files = user_files[user_id]

    for fid in files[-10:]:

        try:

            await client.copy_message(
                message.chat.id,
                config.STORAGE_CHANNEL,
                fid
            )

        except:
            pass


# ================= CREATE LINK =================

@app.on_message(filters.regex("🔗 Create"))
async def create(client, message):

    user_id = message.from_user.id

    if user_id not in user_files:

        return await message.reply(
            "❌ Upload file dulu"
        )

    code = str(user_files[user_id][0])

    user_create[code] = user_files[user_id]

    me = await client.get_me()

    link = f"https://t.me/{me.username}?start={code}"

    await message.reply(
        f"🔗 Link berhasil dibuat\n\n{link}"
    )


# ================= ACCOUNT =================

@app.on_message(filters.regex("👤 Account"))
async def account(client, message):

    user_id = message.from_user.id

    total = 0

    if user_id in user_files:
        total = len(user_files[user_id])

    await message.reply(
        f"👤 User ID: `{user_id}`\n"
        f"📂 Total File: {total}"
    )


# ================= GROUP BUTTON =================

@app.on_message(filters.regex("🔔 Group"))
async def group_button(client, message):

    await message.reply(
        "👥 Join group untuk update",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Join Group", url=config.GROUP_LINK)]
            ]
        )
    )


# ================= BROADCAST =================

broadcast_mode = False

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
