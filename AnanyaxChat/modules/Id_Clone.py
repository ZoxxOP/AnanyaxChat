import logging
import os
import config
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import SessionExpired, AccessTokenInvalid, RPCError
from pyrogram.types import BotCommand

from config import API_HASH, API_ID, OWNER_ID
from AnanyaxChat import AnanyaxChat as app, save_idclonebot_owner
from AnanyaxChat import db as mongodb

# DB collections
IDCLONES = set()
idclonebotdb = mongodb.idclonebotdb


# ------------------------------------------------------
# 🔥 ID Clone Command (String Session Clone)
# ------------------------------------------------------
@app.on_message(filters.command(["idclone", "cloneid"]))
async def idclone_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply_text(
            "**Provide a valid Pyrogram String Session.**\n"
            "Example:\n`/idclone <your pyrogram string>`"
        )

    string_session = " ".join(message.command[1:])
    status = await message.reply_text("⏳ Checking your string session...")

    try:
        # Create temporary client
        temp = Client(
            name=f"idclone_{os.urandom(4).hex()}",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=string_session,
            plugins=dict(root="AnanyaxChat/idchatbot")
        )

        await temp.start()
        user = await temp.get_me()

        await save_idclonebot_owner(user.id, message.from_user.id)

        username = user.username or user.first_name

        details = {
            "user_id": user.id,
            "username": username,
            "name": user.first_name,
            "session": string_session,
        }

        await idclonebotdb.insert_one(details)
        IDCLONES.add(user.id)

        # Notify owner
        await app.send_message(
            OWNER_ID,
            f"🔥 **New ID Clone Added**\n"
            f"👤 User: @{username}\n"
            f"🆔 ID: `{user.id}`"
        )

        await temp.stop()

        await status.edit_text(
            f"✅ ID ChatBot for @{username} successfully cloned.\n\n"
            f"Use /idcloned to list all cloned sessions.\n"
            f"Use `/delidclone <string>` to delete."
        )

    except SessionExpired:
        await status.edit_text("❌ Invalid or expired string session!")
    except AccessTokenInvalid:
        await status.edit_text("❌ Invalid session token!")
    except RPCError as e:
        logging.exception(e)
        await status.edit_text(f"❌ Pyrogram Error:\n`{e}`")
    except Exception as e:
        logging.exception(e)
        await status.edit_text(f"❌ Unexpected Error:\n`{e}`")


# ------------------------------------------------------
# 📋 List all ID clones
# ------------------------------------------------------
@app.on_message(filters.command(["idcloned", "clonedid"]))
async def list_id_clones(client, message):
    bots = await idclonebotdb.find().to_list(None)

    if not bots:
        return await message.reply_text("No ID sessions cloned yet.")

    txt = f"**Total Cloned Sessions:** {len(bots)}\n\n"

    for b in bots:
        txt += (
            f"👤 **{b['name']}**\n"
            f"🆔 `{b['user_id']}`\n"
            f"🔗 @{b['username']}\n\n"
        )

    await message.reply(txt)


# ------------------------------------------------------
# ❌ Delete specific ID clone
# ------------------------------------------------------
@app.on_message(filters.command(["delidclone", "deleteidclone", "cancelidclone"]))
async def delete_id_clone(client, message):
    if len(message.command) < 2:
        return await message.reply_text(
            "**Provide the string session to delete.**\n"
            "Example:\n`/delidclone <string>`"
        )

    session = " ".join(message.command[1:])
    status = await message.reply_text("⏳ Checking session...")

    bot = await idclonebotdb.find_one({"session": session})
    if not bot:
        return await status.edit_text("⚠️ Session not found in cloned list.")

    try:
        await idclonebotdb.delete_one({"session": session})
        IDCLONES.discard(bot["user_id"])

        await status.edit_text("🗑️ Session removed successfully!")

    except Exception as e:
        logging.exception(e)
        await status.edit_text(f"❌ Error removing session:\n`{e}`")


# ------------------------------------------------------
# 🚮 Delete all ID clones (OWNER ONLY)
# ------------------------------------------------------
@app.on_message(filters.command("delallidclone") & filters.user(int(OWNER_ID)))
async def delete_all_id_clones(client, message):
    msg = await message.reply_text("🗑️ Deleting all ID cloned sessions...")
    try:
        await idclonebotdb.delete_many({})
        IDCLONES.clear()
        await msg.edit_text("✅ Cleared all ID cloned sessions.")
    except Exception as e:
        logging.exception(e)
        await msg.edit_text(f"❌ Error:\n`{e}`")


# ------------------------------------------------------
# ♻️ Restart all ID clones after bot restart
# ------------------------------------------------------
async def restart_idchatbots():
    try:
        bots = await idclonebotdb.find().to_list(None)

        for b in bots:
            session = b["session"]

            temp = Client(
                name=f"idclone_restart_{b['user_id']}",
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=session,
                no_updates=False,
                plugins=dict(root="AnanyaxChat/idchatbot")
            )

            try:
                await temp.start()
                await temp.stop()
                IDCLONES.add(b["user_id"])
            except Exception:
                logging.exception("Invalid session found — deleting.")
                await idclonebotdb.delete_one({"session": session})

    except Exception as e:
        logging.exception("Error in restarting ID clones.")
