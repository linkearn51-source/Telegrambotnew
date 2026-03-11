from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
import config
import uuid
import time
import asyncio
import math
import os

app = Client(
    "storagebot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

users=set()
files_db={}
codes={}

# ================= MENU =================

def get_menu(user_id):

    if user_id == config.ADMIN_ID:

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

# ================= PROGRESS =================

async def progress(current,total,message,start):

    now=time.time()
    diff=now-start

    if diff==0:
        return

    percent=current*100/total
    speed=current/diff

    bar="█"*int(percent/5)+"░"*(20-int(percent/5))

    uploaded=current/1024/1024
    total_mb=total/1024/1024
    speed_mb=speed/1024/1024

    try:

        await message.edit(
            f"📤 Uploading\n\n"
            f"[{bar}] {percent:.1f}%\n"
            f"{uploaded:.2f}MB / {total_mb:.2f}MB\n"
            f"⚡ {speed_mb:.2f} MB/s"
        )

    except:
        pass

# ================= START =================

@app.on_message(filters.command("start"))
async def start(client,message):

    users.add(message.from_user.id)

    args=message.text.split()

    if len(args)>1:

        code=args[1]

        if code in codes:

            await send_page(client,message.chat.id,codes[code],0,code)

            return

    await message.reply(
        "📦 **Telegram Storage Bot**\n\n"
        "📤 Upload file\n"
        "🔗 Buat link download\n"
        "📂 Lihat file kamu",
        reply_markup=get_menu(message.from_user.id)
    )

# ================= UPLOAD =================

semaphore = asyncio.Semaphore(10)

@app.on_message(filters.private & (filters.video | filters.document | filters.audio))
async def upload(client,message):

    async with semaphore:

        user=message.from_user.id

        if user not in files_db:
            files_db[user]=[]

        status=await message.reply("📥 Downloading file...")

        start=time.time()

        path=await message.download(
            progress=progress,
            progress_args=(status,start)
        )

        status=await status.edit("📤 Uploading ke storage...")

        start=time.time()

        msg=await client.send_document(
            config.STORAGE_CHANNEL,
            path,
            progress=progress,
            progress_args=(status,start)
        )

        files_db[user].append(msg.id)

        os.remove(path)

        await message.delete()

        await status.edit(
            f"✅ Upload selesai\nTotal file: {len(files_db[user])}"
        )

# ================= CREATE LINK =================

@app.on_message(filters.regex("🔗 Create Link"))
async def create_link(client,message):

    user=message.from_user.id

    if user not in files_db:
        return await message.reply("⚠️ Upload file dulu.")

    code=str(uuid.uuid4())[:8]

    codes[code]=files_db[user]

    bot=await client.get_me()

    link=f"https://t.me/{bot.username}?start={code}"

    await message.reply(
        f"🔗 Link Download:\n\n{link}"
    )

# ================= MY FILES =================

@app.on_message(filters.regex("📂 My Files"))
async def myfiles(client,message):

    user=message.from_user.id

    if user not in files_db:
        return await message.reply("Belum ada file.")

    await send_page(client,message.chat.id,files_db[user],0,"my")

# ================= ACCOUNT =================

@app.on_message(filters.regex("👤 Account"))
async def account(client,message):

    total=len(files_db.get(message.from_user.id,[]))

    await message.reply(
        f"👤 User ID: `{message.from_user.id}`\n"
        f"📂 Total File: {total}"
    )

# ================= PAGINATION =================

async def send_page(client,chat_id,files,page,code):

    per_page=10

    total_pages=math.ceil(len(files)/per_page)

    start=page*per_page
    end=start+per_page

    page_files=files[start:end]

    buttons=[]

    for f in page_files:

        buttons.append([
            InlineKeyboardButton(
                f"🎬 File {f}",
                callback_data=f"get_{f}"
            )
        ])

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

    buttons.append([
        InlineKeyboardButton(
            "👥 Join Group",
            url=config.GROUP_LINK
        )
    ])

    await client.send_message(
        chat_id,
        f"📂 Page {page+1}/{total_pages}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ================= PAGE =================

@app.on_callback_query(filters.regex("^page_"))
async def page(client,query):

    data=query.data.split("_")

    code=data[1]
    page=int(data[2])

    files=codes.get(code)

    if code=="my":
        files=files_db.get(query.from_user.id)

    await query.message.delete()

    await send_page(client,query.message.chat.id,files,page,code)

# ================= DOWNLOAD =================

@app.on_callback_query(filters.regex("^get_"))
async def get_file(client,query):

    file_id=int(query.data.split("_")[1])

    await client.copy_message(
        query.message.chat.id,
        config.STORAGE_CHANNEL,
        file_id
    )

# ================= BROADCAST =================

@app.on_message(filters.regex("📢 Broadcast") & filters.user(config.ADMIN_ID))
async def broadcast(client,message):

    await message.reply("Kirim pesan broadcast sekarang.")

    reply=await client.listen(message.chat.id)

    sent=0

    for u in users:

        try:
            await client.send_message(u,reply.text)
            sent+=1
        except:
            pass

    await message.reply(f"📢 Broadcast terkirim ke {sent} user")

print("Bot running...")

app.run()
