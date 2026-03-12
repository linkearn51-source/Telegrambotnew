from pyrogram import Client, filters
from pyrogram.types import *
import config
import random
import string
import math

app = Client(
    "storagebot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

user_files = {}
created_links = {}
create_count = {}
users = set()
broadcast_mode = {}

PER_PAGE = 10


# ================= MENU =================

def menu(uid):

    if uid == config.ADMIN_ID:

        return ReplyKeyboardMarkup(
            [
                ["▶️ Start", "📤 Upload"],
                ["📂 MyFiles", "👤 Account"],
                ["🔔 Group", "📢 Broadcast"]
            ],
            resize_keyboard=True
        )

    return ReplyKeyboardMarkup(
        [
            ["▶️ Start", "📤 Upload"],
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

        if member.status in ["member", "administrator", "creator"]:
            return True

    except:
        pass

    return False


# ================= START =================

@app.on_message(filters.command("start"))
async def start(client, message):

    uid = message.from_user.id
    users.add(uid)

    args = message.text.split()

    # ===== OPEN LINK =====

    if len(args) > 1:

        code = args[1]

        if code in created_links:

            files = created_links[code]

            await send_page(client, message.chat.id, files, 0, code)

            return

    # ===== NORMAL START =====

    joined = await check_join(client, uid)

    if not joined:

        return await message.reply(
            "⚠️ Kamu harus join group dulu",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("👥 Join Group", url=config.GROUP_LINK)],
                    [InlineKeyboardButton("✅ Verifikasi", callback_data="verify")]
                ]
            )
        )

    await message.reply(
        "📦 Storage Bot\nUpload video untuk menyimpan",
        reply_markup=menu(uid)
    )


# ================= START BUTTON =================

@app.on_message(filters.regex("▶️ Start"))
async def start_btn(client, message):

    uid = message.from_user.id

    joined = await check_join(client, uid)

    if not joined:

        return await message.reply(
            "⚠️ Kamu harus join group dulu",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("👥 Join Group", url=config.GROUP_LINK)],
                    [InlineKeyboardButton("✅ Verifikasi", callback_data="verify")]
                ]
            )
        )

    await message.reply("✅ Bot siap digunakan", reply_markup=menu(uid))


# ================= VERIFY =================

@app.on_callback_query(filters.regex("verify"))
async def verify(client, query):

    joined = await check_join(client, query.from_user.id)

    if joined:

        await query.message.edit("✅ Verifikasi berhasil")

    else:

        await query.answer("❌ Kamu belum join", show_alert=True)


# ================= UPLOAD =================

@app.on_message(filters.regex("📤 Upload"))
async def upload_info(client, message):

    await message.reply("📤 Kirim video atau file ke bot")


@app.on_message(filters.private & (filters.video | filters.document))
async def upload_file(client, message):

    uid = message.from_user.id

    size = message.video.file_size if message.video else message.document.file_size
    size_mb = round(size / 1024 / 1024, 2)

    status = await message.reply("📤 Upload ke storage...")

    sent = await message.copy(config.STORAGE_CHANNEL)

    user_files.setdefault(uid, []).append(sent.id)

    total = len(user_files[uid])

    await status.edit(
        f"✅ Upload berhasil\n\n"
        f"📦 Size: {size_mb} MB\n"
        f"📂 Total File: {total}",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔗 Create Link", callback_data="create")]]
        )
    )


# ================= CREATE LINK =================

@app.on_callback_query(filters.regex("create"))
async def create_link(client, query):

    uid = query.from_user.id

    if uid not in user_files:

        return await query.answer("Upload dulu", show_alert=True)

    files = user_files[uid]

    code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

    created_links[code] = files

    create_count[uid] = create_count.get(uid, 0) + 1

    me = await client.get_me()

    link = f"https://t.me/{me.username}?start={code}"

    await query.message.reply(f"🔗 Link berhasil dibuat\n\n{link}")


# ================= SEND PAGE =================

async def send_page(client, chat_id, files, page, code):

    start = page * PER_PAGE
    end = start + PER_PAGE

    page_files = files[start:end]

    for fid in page_files:

        try:

            await client.copy_message(
                chat_id,
                config.STORAGE_CHANNEL,
                fid
            )

        except:
            pass

    total_pages = math.ceil(len(files) / PER_PAGE)

    buttons = []
    nav = []

    if page > 0:
        nav.append(
            InlineKeyboardButton(
                "⬅ Prev",
                callback_data=f"page_{code}_{page-1}"
            )
        )

    if page < total_pages - 1:
        nav.append(
            InlineKeyboardButton(
                "Next ➡",
                callback_data=f"page_{code}_{page+1}"
            )
        )

    if nav:
        buttons.append(nav)

    buttons.append(
        [InlineKeyboardButton("👥 Join Telegram", url=config.GROUP_LINK)]
    )

    await client.send_message(
        chat_id,
        f"📂 Page {page+1}/{total_pages}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ================= PAGINATION =================

@app.on_callback_query(filters.regex("^page_"))
async def page_handler(client, query):

    data = query.data.split("_")

    code = data[1]
    page = int(data[2])

    files = created_links.get(code)

    if not files:
        return await query.answer("Link expired", show_alert=True)

    await send_page(client, query.message.chat.id, files, page, code)


# ================= MY FILES =================

@app.on_message(filters.regex("📂 MyFiles"))
async def myfiles(client, message):

    uid = message.from_user.id

    files = user_files.get(uid, [])

    total = len(files)

    creates = create_count.get(uid, 0)

    await message.reply(
        f"📂 My Files\n\n"
        f"Total File: {total}\n"
        f"Total Create Link: {creates}"
    )


# ================= ACCOUNT =================

@app.on_message(filters.regex("👤 Account"))
async def account(client, message):

    uid = message.from_user.id

    total = len(user_files.get(uid, []))

    creates = create_count.get(uid, 0)

    await message.reply(
        f"👤 ID: `{uid}`\n"
        f"📂 Total File: {total}\n"
        f"🔗 Total Link: {creates}"
    )


# ================= GROUP =================

@app.on_message(filters.regex("🔔 Group"))
async def group_btn(client, message):

    await message.reply(
        "Join group untuk update",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("👥 Join Telegram", url=config.GROUP_LINK)]]
        )
    )


# ================= BROADCAST =================

@app.on_message(filters.regex("📢 Broadcast"))
async def broadcast_btn(client, message):

    if message.from_user.id != config.ADMIN_ID:
        return

    broadcast_mode[message.from_user.id] = True

    await message.reply("📢 Kirim pesan broadcast")


@app.on_message(filters.private)
async def broadcast_send(client, message):

    uid = message.from_user.id

    if not broadcast_mode.get(uid):
        return

    broadcast_mode[uid] = False

    total = len(users)
    success = 0
    failed = 0

    status = await message.reply("📢 Mengirim broadcast...")

    for user in users:

        try:
            await message.copy(user)
            success += 1
        except:
            failed += 1

    await status.edit(
        f"✅ Broadcast selesai\n\n"
        f"👥 Total user: {total}\n"
        f"✅ Terkirim: {success}\n"
        f"❌ Gagal: {failed}"
    )


print("Bot running...")

app.run()
