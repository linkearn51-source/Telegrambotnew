from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import config
import uuid

app = Client(
    "storagebot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

users = {}
codes = {}

# ======================
# MENU BUTTON
# ======================

def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📤 Upload", callback_data="upload"),
            InlineKeyboardButton("⚙ Create", callback_data="create")
        ],
        [
            InlineKeyboardButton("📂 MyCode", callback_data="mycode"),
            InlineKeyboardButton("👤 MyAccount", callback_data="account")
        ],
        [
            InlineKeyboardButton("📢 Join Group", url=config.GROUP_LINK)
        ]
    ])

# ======================
# START
# ======================

@app.on_message(filters.command("start"))
async def start(client, message):

    args = message.text.split()

    # open link code
    if len(args) > 1:

        code = args[1]

        if code in codes:

            files = codes[code]

            for file_id in files:

                await app.copy_message(
                    message.chat.id,
                    config.STORAGE_CHANNEL,
                    file_id
                )

            return

    # force join
    try:
        await client.get_chat_member(config.FORCE_CHANNEL, message.from_user.id)
    except:
        btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{config.FORCE_CHANNEL.replace('@','')}")]]
        )
        return await message.reply(
            "⚠️ Join channel dulu",
            reply_markup=btn
        )

    await message.reply(
        "📦 File Storage Bot\n\nPilih menu:",
        reply_markup=main_menu()
    )

# ======================
# BUTTON HANDLER
# ======================

@app.on_callback_query()
async def buttons(client, query):

    user = query.from_user.id

    if query.data == "upload":

        users[user] = []

        await query.message.reply(
            "📤 Kirim video / file sekarang"
        )

    elif query.data == "create":

        if user not in users or len(users[user]) == 0:
            return await query.answer("Upload file dulu", True)

        code = str(uuid.uuid4())[:8]

        codes[code] = users[user]

        bot = await app.get_me()

        link = f"https://t.me/{bot.username}?start={code}"

        await query.message.reply(
            f"✅ Link berhasil dibuat\n\n"
            f"🔑 Code : `{code}`\n"
            f"🔗 Link : {link}"
        )

    elif query.data == "account":

        total = len(users.get(user, []))

        await query.message.reply(
            f"👤 User ID : {user}\n"
            f"📂 Upload : {total} file"
        )

    elif query.data == "mycode":

        text = "📂 Code kamu:\n\n"

        for c in codes:

            text += f"`{c}`\n"

        await query.message.reply(text)

# ======================
# FILE UPLOAD
# ======================

@app.on_message(filters.private & (filters.video | filters.document | filters.audio))
async def save_file(client, message):

    user = message.from_user.id

    if user not in users:
        return

    progress = await message.reply("⬆️ Uploading...")

    msg = await message.forward(config.STORAGE_CHANNEL)

    users[user].append(msg.id)

    total = len(users[user])

    await progress.edit(
        f"✅ Upload selesai\n"
        f"📂 Total file : {total}"
    )

# ======================
# BROADCAST ADMIN
# ======================

@app.on_message(filters.command("broadcast") & filters.user(config.ADMIN_ID))
async def broadcast(client, message):

    if len(message.text.split()) < 2:
        return await message.reply("Gunakan:\n/broadcast pesan")

    text = message.text.split(None,1)[1]

    for user in users:

        try:
            await app.send_message(user, text)
        except:
            pass

    await message.reply("✅ Broadcast selesai")

app.run()
