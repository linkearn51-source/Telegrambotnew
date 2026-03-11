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

user_files = {}
codes = {}
users = set()

# ================= MENU =================

def menu():
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

# ================= START =================

@app.on_message(filters.command("start"))
async def start(client, message):

    user = message.from_user.id
    users.add(user)

    args = message.text.split()

    # open download link
    if len(args) > 1:

        code = args[1]

        if code in codes:

            files = codes[code]

            for f in files:

                await app.copy_message(
                    message.chat.id,
                    config.STORAGE_CHANNEL,
                    f
                )

            return

    # force join
    try:
        await client.get_chat_member(config.FORCE_CHANNEL, user)
    except:
        btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton(
                "Join Channel",
                url=f"https://t.me/{config.FORCE_CHANNEL.replace('@','')}"
            )]]
        )

        return await message.reply(
            "⚠️ Join channel dulu",
            reply_markup=btn
        )

    await message.reply(
        "📦 File Storage Bot\n\nPilih menu:",
        reply_markup=menu()
    )

# ================= BUTTON =================

@app.on_callback_query()
async def buttons(client, query):

    user = query.from_user.id

    if query.data == "upload":

        user_files[user] = []

        await query.message.reply("📤 Kirim file/video sekarang")

    elif query.data == "create":

        if user not in user_files or len(user_files[user]) == 0:
            return await query.answer("Upload dulu", True)

        code = str(uuid.uuid4())[:8]

        codes[code] = user_files[user]

        bot = await app.get_me()

        link = f"https://t.me/{bot.username}?start={code}"

        await query.message.reply(
            f"✅ Link dibuat\n\n"
            f"Code : `{code}`\n"
            f"Link : {link}"
        )

    elif query.data == "account":

        total = len(user_files.get(user, []))

        await query.message.reply(
            f"👤 User ID : {user}\n"
            f"📂 Upload : {total} file"
        )

    elif query.data == "mycode":

        text = "📂 Code kamu:\n\n"

        for c in codes:
            text += f"`{c}`\n"

        await query.message.reply(text)

# ================= FILE UPLOAD =================

@app.on_message(filters.private & (filters.video | filters.document | filters.audio))
async def save_file(client, message):

    user = message.from_user.id

    if user not in user_files:
        return

    status = await message.reply("⬆️ Uploading...")

    msg = await app.copy_message(
        config.STORAGE_CHANNEL,
        message.chat.id,
        message.id
    )

    user_files[user].append(msg.id)

    total = len(user_files[user])

    await status.edit(
        f"✅ Upload selesai\n"
        f"Total file : {total}"
    )

# ================= BROADCAST =================

@app.on_message(filters.command("broadcast") & filters.user(config.ADMIN_ID))
async def broadcast(client, message):

    if len(message.text.split()) < 2:
        return await message.reply("Gunakan:\n/broadcast pesan")

    text = message.text.split(None,1)[1]

    for u in users:

        try:
            await app.send_message(u, text)
        except:
            pass

    await message.reply("✅ Broadcast selesai")

app.run()
