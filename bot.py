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

start_buttons = InlineKeyboardMarkup([
[
InlineKeyboardButton("Upload", callback_data="upload"),
InlineKeyboardButton("Create", callback_data="create")
],
[
InlineKeyboardButton("My Code", callback_data="mycode"),
InlineKeyboardButton("My Account", callback_data="account")
]
])

@app.on_message(filters.command("start"))
async def start(client, message):

    try:
        await client.get_chat_member(config.FORCE_CHANNEL, message.from_user.id)
    except:
        join = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{config.FORCE_CHANNEL.replace('@','')}")]]
        )
        return await message.reply("Join channel dulu", reply_markup=join)

    await message.reply(
        "Welcome\nSilakan pilih menu",
        reply_markup=start_buttons
    )

@app.on_callback_query()
async def callback(client, query):

    user = query.from_user.id

    if query.data == "upload":
        user_files[user] = []
        await query.message.reply("Silakan kirim video/file")

    elif query.data == "create":

        if user not in user_files or len(user_files[user]) == 0:
            return await query.answer("Upload dulu", True)

        code = str(uuid.uuid4())[:8]

        codes[code] = user_files[user]

        link = f"https://t.me/{(await app.get_me()).username}?start={code}"

        await query.message.reply(
            f"File berhasil dibuat\n\nCode : `{code}`\nLink : {link}",
            disable_web_page_preview=True
        )

    elif query.data == "account":

        total = len(user_files.get(user, []))

        await query.message.reply(
            f"User ID : {user}\nTotal Upload : {total}"
        )

@app.on_message(filters.command("test"))
async def test(client, message):
    chat = await client.get_chat(config.STORAGE_CHANNEL)
    await message.reply(f"Channel ditemukan: {chat.title}")
    
@app.on_message(filters.video | filters.document | filters.audio)
async def save_file(client, message):

    user = message.from_user.id

    if user not in user_files:
        return

    msg = await message.forward(config.STORAGE_CHANNEL)

    user_files[user].append(msg.id)

    total = len(user_files[user])

    await message.reply(
        f"Upload berhasil\nTotal file : {total}"
    )

@app.on_message(filters.command("broadcast") & filters.user(config.ADMIN_ID))
async def broadcast(client, message):

    text = message.text.split(None,1)[1]

    users = list(user_files.keys())

    for u in users:
        try:
            await app.send_message(u,text)
        except:
            pass

    await message.reply("Broadcast selesai")

@app.on_message(filters.private & filters.command("start") & filters.regex(r"/start (.*)"))
async def get_files(client,message):

    code = message.text.split(" ")[1]

    if code not in codes:
        return await message.reply("Code tidak valid")

    files = codes[code]

    for f in files:
        await app.copy_message(
            message.chat.id,
            config.STORAGE_CHANNEL,
            f
        )

app.run()
