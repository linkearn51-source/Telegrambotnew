from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
import config
import time
import uuid
import math
import os

app = Client(
    "storagebot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

users=set()
user_files={}
codes={}
upload_time={}

# ================= COMMAND MENU =================

@app.on_message(filters.command("start"))
async def start(client,message):

    await client.set_bot_commands([
        BotCommand("start","Start bot"),
        BotCommand("upload","Upload file"),
        BotCommand("create","Create link"),
        BotCommand("myaccount","My account"),
        BotCommand("mylink","My links"),
        BotCommand("broadcast","Admin broadcast")
    ])

    await message.reply(
        "📦 **Premium File Storage Bot**\n\n"
        "Upload file lalu buat link download.",
        reply_markup=menu()
    )

# ================= MENU =================

def menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📤 Upload File",callback_data="upload"),
            InlineKeyboardButton("🔗 Create Link",callback_data="create")
        ],
        [
            InlineKeyboardButton("📂 My Files",callback_data="files"),
            InlineKeyboardButton("👤 My Account",callback_data="account")
        ],
        [
            InlineKeyboardButton("📢 Channel",url=config.GROUP_LINK)
        ]
    ])

# ================= PROGRESS =================

async def progress(current,total,message,start):

    now=time.time()
    diff=now-start

    if diff==0:
        return

    speed=current/diff
    percent=current*100/total

    bar="█"*int(percent/5)+"░"*(20-int(percent/5))

    uploaded=current/1024/1024
    total_mb=total/1024/1024
    speed_mb=speed/1024/1024

    try:
        await message.edit(
            f"📤 **Uploading File**\n\n"
            f"[{bar}] {percent:.2f}%\n\n"
            f"📦 {uploaded:.2f}MB / {total_mb:.2f}MB\n"
            f"⚡ Speed {speed_mb:.2f} MB/s",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Create Link",callback_data="create")]
            ])
        )
    except:
        pass

# ================= UPLOAD =================

@app.on_message(filters.private & (filters.video | filters.document | filters.audio))
async def upload(client,message):

    user=message.from_user.id

    if user not in user_files:
        user_files[user]=[]

    status=await message.reply("📥 Downloading file...")

    start=time.time()

    file_path=await message.download(
        progress=progress,
        progress_args=(status,start)
    )

    status=await status.edit("📤 Uploading ke storage...")

    start=time.time()

    msg=await client.send_document(
        config.STORAGE_CHANNEL,
        file_path,
        progress=progress,
        progress_args=(status,start)
    )

    user_files[user].append(msg.id)

    os.remove(file_path)

    await status.edit(
        f"✅ Upload selesai\n"
        f"Total file: {len(user_files[user])}",
        reply_markup=menu()
    )

# ================= CREATE LINK =================

@app.on_message(filters.command("create"))
async def create_link(client,message):

    user=message.from_user.id

    if user not in user_files:
        return await message.reply("Upload file dulu")

    code=str(uuid.uuid4())[:8]

    codes[code]=user_files[user]

    bot=await client.get_me()

    link=f"https://t.me/{bot.username}?start={code}"

    await message.reply(
        f"🔗 **Link Download**\n\n{link}"
    )

# ================= START LINK =================

@app.on_message(filters.command("start") & filters.private)
async def start_link(client,message):

    args=message.text.split()

    if len(args)<2:
        return

    code=args[1]

    if code not in codes:
        return await message.reply("Link tidak valid")

    files=codes[code]

    await send_page(message,files,0)

# ================= PAGINATION =================

async def send_page(message,files,page):

    per_page=10
    pages=math.ceil(len(files)/per_page)

    start=page*per_page
    end=start+per_page

    buttons=[]

    for f in files[start:end]:

        buttons.append([
            InlineKeyboardButton(
                f"📄 File {f}",
                callback_data=f"get_{f}"
            )
        ])

    nav=[]

    if page>0:
        nav.append(InlineKeyboardButton("⬅ Prev",callback_data=f"page_{page-1}"))

    if page<pages-1:
        nav.append(InlineKeyboardButton("Next ➡",callback_data=f"page_{page+1}"))

    if nav:
        buttons.append(nav)

    buttons.append([
        InlineKeyboardButton("📢 Channel",url=config.GROUP_LINK)
    ])

    await message.reply(
        "📂 Download Files",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ================= PAGE BUTTON =================

@app.on_callback_query(filters.regex("page_"))
async def page(client,query):

    page=int(query.data.split("_")[1])

    user=query.from_user.id

    files=[]

    for c in codes.values():
        files=c

    await send_page(query.message,files,page)

# ================= GET FILE =================

@app.on_callback_query(filters.regex("get_"))
async def get_file(client,query):

    file_id=int(query.data.split("_")[1])

    await client.copy_message(
        query.message.chat.id,
        config.STORAGE_CHANNEL,
        file_id
    )

# ================= ACCOUNT =================

@app.on_message(filters.command("myaccount"))
async def account(client,message):

    user=message.from_user.id

    total=len(user_files.get(user,[]))

    await message.reply(
        f"👤 User ID : `{user}`\n"
        f"📂 Total File : {total}"
    )

# ================= BROADCAST =================

@app.on_message(filters.command("broadcast") & filters.user(config.ADMIN_ID))
async def broadcast(client,message):

    text=message.text.split(None,1)[1]

    sent=0

    for u in users:

        try:
            await client.send_message(u,text)
            sent+=1
        except:
            pass

    await message.reply(f"📢 Broadcast terkirim {sent}")

print("Bot running...")

app.run()
