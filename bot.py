from pyrogram import Client,filters
from pyrogram.types import *
import config
import database as db
import uuid
import math

app = Client(
    "storagebot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

# MENU

def menu(uid):

    if str(uid)==str(config.ADMIN_ID):

        return ReplyKeyboardMarkup(
            [
                ["📤 Upload","🔗 Create Link"],
                ["📂 My Files","👤 Account"],
                ["📢 Broadcast"]
            ],
            resize_keyboard=True
        )

    else:

        return ReplyKeyboardMarkup(
            [
                ["📤 Upload","🔗 Create Link"],
                ["📂 My Files","👤 Account"]
            ],
            resize_keyboard=True
        )

# START

@app.on_message(filters.command("start"))
async def start(client,message):

    uid=str(message.from_user.id)

    db.users[uid]=True
    db.save_all()

    args=message.text.split()

    if len(args)>1:

        code=args[1]

        if code in db.codes:

            await send_page(client,message.chat.id,db.codes[code],0,code)
            return

    await message.reply(
        "📦 Telegram Storage Bot\nUpload video lalu buat link download",
        reply_markup=menu(uid)
    )

# UPLOAD

@app.on_message(filters.private & (filters.video | filters.document))
async def upload(client,message):

    uid=str(message.from_user.id)

    status=await message.reply("📤 Menyimpan file...")

    thumb=None

    if message.video and message.video.thumbs:

        thumb_file=await client.download_media(message.video.thumbs[0])
        thumb=thumb_file

    copy=await message.copy(
        config.STORAGE_CHANNEL,
        thumb=thumb
    )

    if uid not in db.files:
        db.files[uid]=[]

    db.files[uid].append(copy.id)

    db.save_all()

    await status.edit("✅ File berhasil disimpan")

# CREATE LINK

@app.on_message(filters.regex("🔗 Create Link"))
async def createlink(client,message):

    uid=str(message.from_user.id)

    if uid not in db.files:

        return await message.reply("Upload file dulu.")

    code=str(uuid.uuid4())[:8]

    db.codes[code]=db.files[uid]

    db.save_all()

    me=await client.get_me()

    link=f"https://t.me/{me.username}?start={code}"

    await message.reply(
        f"🔗 Link kamu:\n\n{link}"
    )

# MY FILES

@app.on_message(filters.regex("📂 My Files"))
async def myfiles(client,message):

    uid=str(message.from_user.id)

    if uid not in db.files:

        return await message.reply("Belum ada file.")

    await send_page(client,message.chat.id,db.files[uid],0,"my")

# ACCOUNT

@app.on_message(filters.regex("👤 Account"))
async def account(client,message):

    uid=str(message.from_user.id)

    total=len(db.files.get(uid,[]))

    await message.reply(
        f"👤 ID: `{uid}`\n"
        f"📂 Total file: {total}"
    )

# PAGINATION

async def send_page(client,chat_id,files,page,code):

    per_page=10

    total_pages=math.ceil(len(files)/per_page)

    start=page*per_page
    end=start+per_page

    page_files=files[start:end]

    buttons=[]

    for f in page_files:

        buttons.append(
            [InlineKeyboardButton(
                f"🎬 Video {f}",
                callback_data=f"get_{f}"
            )]
        )

    nav=[]

    if page>0:

        nav.append(
            InlineKeyboardButton(
                "⬅ Prev",
                callback_data=f"page_{code}_{page-1}"
            )
        )

    if page<total_pages-1:

        nav.append(
            InlineKeyboardButton(
                "Next ➡",
                callback_data=f"page_{code}_{page+1}"
            )
        )

    if nav:
        buttons.append(nav)

    buttons.append(
        [InlineKeyboardButton(
            "👥 Join Group",
            url=config.GROUP_LINK
        )]
    )

    await client.send_message(
        chat_id,
        f"📂 Page {page+1}/{total_pages}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# PAGE BUTTON

@app.on_callback_query(filters.regex("^page_"))
async def page(client,query):

    data=query.data.split("_")

    code=data[1]
    page=int(data[2])

    if code=="my":
        files=db.files.get(str(query.from_user.id))
    else:
        files=db.codes.get(code)

    await query.message.delete()

    await send_page(client,query.message.chat.id,files,page,code)

# VIDEO BUTTON

@app.on_callback_query(filters.regex("^get_"))
async def getfile(client,query):

    fid=int(query.data.split("_")[1])

    await client.copy_message(
        query.message.chat.id,
        config.STORAGE_CHANNEL,
        fid
    )

# BROADCAST

@app.on_message(filters.regex("📢 Broadcast") & filters.user(config.ADMIN_ID))
async def broadcast(client,message):

    ask=await message.reply("Kirim pesan broadcast.")

    msg=await client.listen(message.chat.id)

    total=0

    for uid in db.users:

        try:

            await client.send_message(uid,msg.text)
            total+=1

        except:
            pass

    await ask.edit(f"Broadcast terkirim ke {total} user")

print("Bot running...")

app.run()
