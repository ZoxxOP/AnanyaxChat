from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import ChatAdminRequired, UserNotParticipant, ChatWriteForbidden
from AnanyaxChat import AnanyaxChat as app
from config import UPDATE_CHNL as MUST_JOIN, OWNER_ID


@app.on_message(filters.incoming & filters.private, group=-1)
async def must_join_channel(app: Client, msg: Message):
    # 🚨 Bypass must_join for OWNER
    if msg.from_user and msg.from_user.id == int(OWNER_ID):
        return

    if not MUST_JOIN:
        return

    try:
        try:
            await app.get_chat_member(MUST_JOIN, msg.from_user.id)
        except UserNotParticipant:
            if MUST_JOIN.isalpha():
                link = "https://t.me/" + MUST_JOIN
            else:
                chat_info = await app.get_chat(MUST_JOIN)
                link = chat_info.invite_link

            try:
                await msg.reply_photo(
                    photo="https://files.catbox.moe/5lmkua.jpg",
                    caption=(
                        f"**👋 ʜᴇʟʟᴏ {msg.from_user.mention},**\n\n"
                        f"**ʏᴏᴜ ɴᴇᴇᴅ ᴛᴏ ᴊᴏɪɴ ᴛʜᴇ [ᴄʜᴀɴɴᴇʟ]({link}) ᴛᴏ sᴇɴᴅ ᴍᴇssᴀɢᴇs ɪɴ ᴛʜɪs ʙᴏᴛ.**"
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("๏ ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ ๏", url=link)]]
                    )
                )
                await msg.stop_propagation()
            except ChatWriteForbidden:
                pass
    except ChatAdminRequired:
        print(f"๏ᴘʀᴏᴍᴏᴛᴇ ᴍᴇ ᴀs ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴇ ᴍᴜsᴛ_Jᴏɪɴ ᴄʜᴀᴛ ๏: {MUST_JOIN} !")
