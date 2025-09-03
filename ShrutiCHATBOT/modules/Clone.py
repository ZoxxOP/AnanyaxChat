import logging
import config
import asyncio
from pyrogram import Client, filters
from pyrogram.errors.exceptions.bad_request_400 import AccessTokenInvalid
from config import API_HASH, API_ID, OWNER_ID
from ShrutiCHATBOT import ShrutiCHATBOT as app, save_clonebot_owner, save_idclonebot_owner
from ShrutiCHATBOT import db as mongodb

IDCLONES = set()
BOTCLONES = set()

idclonebotdb = mongodb.idclonebotdb
botclonebotdb = mongodb.botclonebotdb   # ✅ new DB for bot-token clones


# ✅ Bot Token Clone Command
@app.on_message(filters.command(["clone"]))
async def clone_bot_token(client, message):
    if len(message.command) < 2:
        await message.reply_text(
            "**⚠️ Please provide a bot token after the command.**\n\n"
            "**Example:** `/clone <bot_token>`"
        )
        return

    bot_token = message.command[1]
    mi = await message.reply_text("**Checking your Bot Token...**")

    try:
        ai = Client(
            name=f"bot_{message.from_user.id}",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=bot_token,
            no_updates=False,
            plugins=dict(root="ShrutiCHATBOT.botchatbot"),
        )
        await ai.start()
        user = await ai.get_me()
        clone_id = user.id
        username = user.username or user.first_name

        await save_clonebot_owner(clone_id, message.from_user.id)

        details = {
            "user_id": user.id,
            "username": username,
            "name": user.first_name,
            "token": bot_token,
        }

        await botclonebotdb.insert_one(details)
        BOTCLONES.add(user.id)

        await mi.edit_text(
            f"**Bot @{username} cloned successfully ✅.**\n"
            f"**Remove clone by:** /delclone\n**Check all cloned bots by:** /cloned"
        )
    except Exception as e:
        logging.exception("Error during bot cloning.")
        await mi.edit_text(f"**Invalid Bot Token:** `{e}`")


# ✅ Pyrogram String Session Clone Command
@app.on_message(filters.command(["idclone", "cloneid"]))
async def clone_string_session(client, message):
    if len(message.command) < 2:
        await message.reply_text(
            "**⚠️ Please provide a string session after the command.**\n\n"
            "**Example:** `/idclone <string_session>`"
        )
        return

    string_session = " ".join(message.command[1:])
    mi = await message.reply_text("**Checking your String Session...**")

    try:
        ai = Client(
            name=f"user_{message.from_user.id}",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=string_session,
            no_updates=False,
            plugins=dict(root="ShrutiCHATBOT.idchatbot"),
        )
        await ai.start()
        user = await ai.get_me()
        clone_id = user.id
        username = user.username or user.first_name

        await save_idclonebot_owner(clone_id, message.from_user.id)

        details = {
            "user_id": user.id,
            "username": username,
            "name": user.first_name,
            "session": string_session,
        }

        await idclonebotdb.insert_one(details)
        IDCLONES.add(user.id)

        await mi.edit_text(
            f"**Session for @{username} cloned successfully ✅.**\n"
            f"**Remove clone by:** /delidclone\n**Check all cloned sessions by:** /idcloned"
        )
    except AccessTokenInvalid:
        await mi.edit_text("**Invalid String Session. Please provide a valid one.**")
    except Exception as e:
        logging.exception("Error during session cloning.")
        await mi.edit_text(f"**Invalid String Session:** `{e}`")
