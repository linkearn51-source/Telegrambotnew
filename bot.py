from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import config
import uuid
import time
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

# ================= UI MENU =================

def menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📤 Upload",callback_data="upload"),
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

    percent=current*100/total
    speed=current/diff

    bar="█"*int(percent/5)+"░"*(20-int(percent/5))

    uploaded=current/1024/1024
    total_mb=total/1024/1024
    speed_mb=speed/1024/1024

    try:

        await message.edit(
            f"📤 **Uploading File**\n\n"
            f"[{bar}] {percent:.2f}%\n\n"
            f"📦 {uploaded:.2f}MB / {total_mb:.2f}MB\n"
            f"⚡ Speed: {speed_mb:.2f} MB/s",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Create Link",callback_data="create")]
            ])
        )

    except:
        pass

# ================= FORCE JOIN =================

async def force_join(client,message):

    user=message.from_user.id

    try:
        await client.get_chat_member(config.FORCE_CHANNEL,user)
        return True

    except:

        btn=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "📢 Join Channel",
                    url=f"https://t.me/{config.FORCE_CHANNEL.replace('@','')}"
                )
            ],
            [
                InlineKeyboardButton(
                    "✅ Verifikasi",
                    callback_data="verify"
                )
            ]
        ])

        await message.reply(
            "⚠️ Kamu harus join channel terlebih dahulu untuk menggunakan bot.",
            reply_markup=btn
        )

        return False

# ================= START =================

@app.on_message(filters.command("start") & filters.private)
async def start(client,message):

    ok=await force_join(client,message)

    if not ok:
        return

    users.add(message.from_user.id)

    args=message.text.split()

    if len(args)>1:

        code=args[1]

        if code in codes:

            files=codes[code]

            await send_page(message,files,0)

            return

    await message.reply(
        "📦 **Premium File Storage Bot**\n\n"
        "Upload file lalu buat link download.",
        reply_markup=menu()
    )

# ================= VERIFY =================

@app.on_callback_query(filters.regex("verify"))
async def verify(client,query):

    user=query.from_user.id

    try:

        await client.get_chat_member(config.FORCE_CHANNEL,user)

        await query.message.edit(
            "✅ Verifikasi berhasil!\n\nBot sudah bisa digunakan.",
            reply_markup=menu()
        )

    except:

        await query.answer("Kamu belum join channel!",True)

# ================= COMMAND UPLOAD =================

@app.on_message(filters.command("upload"))
async def cmd_upload(client,message):

    await message.reply(
        "📤 Kirim file/video sekarang",
        reply_markup=menu()
    )

# ================= FILE UPLOAD =================

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

    await message.delete()

    await status.edit(
        f"✅ Upload selesai\nTotal file: {len(user_files[user])}",
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
        f"👤 User ID : `{user}`\n📂 Total File : {total}"
    )

# ================= MY LINK =================

@app.on_message(filters.command("mylink"))
async def mylink(client,message):

    bot=await client.get_me()

    links=[]

    for c in codes:
        links.append(f"https://t.me/{bot.username}?start={c}")

    text="\n".join(links)

    if not text:
        text="Belum ada link"

    await message.reply(text)

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

    await message.reply(f"📢 Broadcast terkirim {sent} user")

print("Bot running...")

app.run()
