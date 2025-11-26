from pyrogram import Client, filters
from pyrogram.types import Message
from AnanyaxChat import AnanyaxChat as app, mongo, db
import asyncio
from AnanyaxChat.modules.helpers import chatai, CHATBOT_ON
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

# 🟢 Chat language database
lang_db = db.ChatLangDb.LangCollection
message_cache = {}

# 🟢 Get language for chat
async def get_chat_language(chat_id):
    chat_lang = await lang_db.find_one({"chat_id": chat_id})
    return chat_lang["language"] if chat_lang and "language" in chat_lang else None

# 🟢 Store message history for auto-language detection
@app.on_message(filters.text, group=2)
async def store_messages(client, message: Message):
    global message_cache

    chat_id = message.chat.id
    chat_lang = await get_chat_language(chat_id)

    # If language already set → skip
    if chat_lang and chat_lang != "nolang":
        return 

    # Ignore bot messages
    if message.from_user and message.from_user.is_bot:
        return

    # Create chat cache
    if chat_id not in message_cache:
        message_cache[chat_id] = []

    message_cache[chat_id].append(message)

    # Detect language when 30 msgs collected
    if len(message_cache[chat_id]) >= 30:
        history = "\n\n".join(
            [f"Text: {msg.text}..." for msg in message_cache[chat_id]]
        )

        user_input = f"""
        Sentences list:
        [
        {history}
        ]

        Analyze each sentence separately and detect the dominant language.
        Provide only:
        Lang Name :- ""
        Lang Code :- ""
        """

        # 🛑 Removed MukeshAPI → replacing with chatai
        response = await chatai(user_input)

        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("sᴇʟᴇᴄᴛ ʟᴀɴɢᴜᴀɢᴇ", callback_data="choose_lang")]]
        )

        await message.reply_text(
            f"**Chat language detected for this chat:**\n\n{response}\n\n"
            f"Use /lang to set language.",
            reply_markup=reply_markup
        )

        message_cache[chat_id].clear()

# 🟢 Show current language
@app.on_message(filters.command("chatlang"))
async def fetch_chat_lang(client, message):
    chat_id = message.chat.id
    chat_lang = await get_chat_language(chat_id)

    await message.reply_text(
        f"The current language code for this chat is: **{chat_lang}**"
    )
