from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import config
import time
import uuid
import math

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
            f"⬆ Uploading\n\n"
            f"[{bar}] {percent:.2f}%\n\n"
            f"{uploaded:.2f}MB / {total_mb:.2f}MB\n"
            f"Speed: {speed_mb:.2f} MB/s"
        )
    except:
        pass

# ================= MENU =================

def menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📤 Upload",callback_data="upload"),
            InlineKeyboardButton("⚙ Create Link",callback_data="create")
        ],
        [
            InlineKeyboardButton("📂 My Files",callback_data="files"),
            InlineKeyboardButton("👤 Account",callback_data="account")
        ],
        [
            InlineKeyboardButton("📢 Group",url=config.GROUP_LINK)
        ]
    ])

# ================= START =================

@app.on_message(filters.private & filters.command("start"))
async def start(client,message):

    user=message.from_user.id
    users.add(user)

    args=message.text.split()

    if len(args)>1:

        code=args[1]

        if code in codes:

            files=codes[code]

            for f in files:

                await client.copy_message(
                    message.chat.id,
                    config.STORAGE_CHANNEL,
                    f
                )

            return

    try:
        await client.get_chat_member(config.FORCE_CHANNEL,user)

    except:

        btn=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "Join Channel",
                    url=f"https://t.me/{config.FORCE_CHANNEL.replace('@','')}"
                )
            ]
        ])

        return await message.reply(
            "⚠️ Join channel dulu",
            reply_markup=btn
        )

    await message.reply(
        "📦 **File Storage Bot**\n\n"
        "Upload file lalu buat link download.",
        reply_markup=menu()
    )

# ================= BUTTON =================

@app.on_callback_query()
async def buttons(client,query):

    user=query.from_user.id

    if query.data=="upload":

        user_files[user]=[]

        await query.message.reply(
            "📤 Kirim file/video sekarang"
        )

    elif query.data=="create":

        if user not in user_files or len(user_files[user])==0:
            return await query.answer("Upload dulu",True)

        code=str(uuid.uuid4())[:8]

        codes[code]=user_files[user]

        bot=await client.get_me()

        link=f"https://t.me/{bot.username}?start={code}"

        await query.message.reply(
            f"✅ Link dibuat\n\n"
            f"Code : `{code}`\n"
            f"Link : {link}"
        )

    elif query.data=="account":

        total=len(user_files.get(user,[]))

        await query.message.reply(
            f"👤 User ID : `{user}`\n"
            f"📂 File : {total}"
        )

    elif query.data=="files":

        await show_files(query,user,0)

# ================= PAGINATION =================

async def show_files(query,user,page):

    files=user_files.get(user,[])

    if not files:
        return await query.message.reply("Belum ada file")

    per_page=10
    pages=math.ceil(len(files)/per_page)

    start=page*per_page
    end=start+per_page

    buttons=[]

    for f in files[start:end]:

        buttons.append([
            InlineKeyboardButton(
                f"📄 File {f}",
                callback_data=f"file_{f}"
            )
        ])

    nav=[]

    if page>0:
        nav.append(
            InlineKeyboardButton("⬅",callback_data=f"page_{page-1}")
        )

    if page<pages-1:
        nav.append(
            InlineKeyboardButton("➡",callback_data=f"page_{page+1}")
        )

    if nav:
        buttons.append(nav)

    await query.message.reply(
        "📂 File kamu:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@app.on_callback_query(filters.regex("page_"))
async def page(client,query):

    page=int(query.data.split("_")[1])
    user=query.from_user.id

    await show_files(query,user,page)

# ================= FILE BUTTON =================

@app.on_callback_query(filters.regex("file_"))
async def file_button(client,query):

    file_id=int(query.data.split("_")[1])

    bot=await client.get_me()

    code=str(uuid.uuid4())[:8]

    codes[code]=[file_id]

    link=f"https://t.me/{bot.username}?start={code}"

    await query.message.reply(
        f"🔗 Download Link\n\n{link}"
    )

# ================= FILE UPLOAD =================

@app.on_message(filters.private & (filters.video | filters.document | filters.audio))
async def upload(client,message):

    user = message.from_user.id

    if user not in user_files:
        return await message.reply("Klik Upload dulu")

    now = time.time()

    if user in upload_time:
        if now - upload_time[user] < 5:
            return await message.reply("⏳ Tunggu 5 detik sebelum upload lagi")

    upload_time[user] = now

    status = await message.reply("📤 Uploading ke storage...")

    msg = await client.copy_message(
        config.STORAGE_CHANNEL,
        message.chat.id,
        message.id
    )

    user_files[user].append(msg.id)

    total = len(user_files[user])

    await status.edit(
        f"✅ Upload selesai\n"
        f"Total file: {total}"
                      )

# ================= BROADCAST =================

@app.on_message(filters.command("broadcast") & filters.user(config.ADMIN_ID))
async def broadcast(client,message):

    if len(message.text.split())<2:
        return await message.reply("/broadcast pesan")

    text=message.text.split(None,1)[1]

    sent=0

    for u in users:

        try:
            await client.send_message(u,text)
            sent+=1
        except:
            pass

    await message.reply(
        f"📢 Broadcast terkirim {sent} user"
    )

print("Bot running...")

app.run()
