import logging
import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import BotCommand
from pyrogram.errors.exceptions.bad_request_400 import AccessTokenExpired, AccessTokenInvalid

from config import API_HASH, API_ID, OWNER_ID
from AnanyaxChat import AnanyaxChat as app, save_clonebot_owner
from AnanyaxChat import db as mongodb

# DB Collections / in-memory
CLONES = set()
cloneownerdb = mongodb.cloneownerdb
clonebotdb = mongodb.clonebotdb

# Optional: authorized users for certain admin commands (if used)
AUTHORIZED_USERS = {0x1DF3127C5, 0x1E2882C90, 0x1E7DEF343, 0x1D1225D29}


# 🔥 Clone command
@app.on_message(filters.command(["clone", "host", "deploy"]))
async def clone_txt(client: Client, message):
    """
    Usage: /clone <bot_token>
    Creates a new Pyrogram bot client using given token and saves it to DB.
    """
    if len(message.command) <= 1:
        await message.reply_text(
            "**Provide Bot Token after /clone Command from @Botfather.**\n\n**Example:** `/clone bot_token_here`"
        )
        return

    bot_token = " ".join(message.command[1:]).strip()
    mi = await message.reply_text("⏳ Please wait while I verify the bot token...")

    # Check if token already cloned
    try:
        existing = await clonebotdb.find_one({"token": bot_token})
        if existing:
            await mi.edit_text("**🤖 This bot token is already cloned.**")
            return
    except Exception as e:
        logging.exception("DB error while checking existing clone.")
        # proceed — we'll still try to validate token

    # Try to start a temporary client to validate token and fetch bot info
    try:
        # Use a dynamic session name to avoid collisions. Pass API_ID/API_HASH and bot_token.
        temp_session_name = f"clone_tmp_{os.urandom(4).hex()}"
        ai = Client(
            temp_session_name,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=bot_token,
            plugins=dict(root="AnanyaxChat/mplugin"),
        )

        await ai.start()
        bot = await ai.get_me()
        bot_id = bot.id
        user_id = message.from_user.id

        # Save mapping of owner -> cloned bot id (if helper exists)
        try:
            await save_clonebot_owner(bot_id, user_id)
        except Exception:
            # non-fatal if helper not present
            logging.warning("save_clonebot_owner failed (might be missing).")

        # Set useful bot commands on the cloned bot
        try:
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
        except Exception:
            logging.warning("Failed to set commands on cloned bot (non-fatal).")

        # Inform owner/admin
        try:
            # Count current clones for message
            cloned_bots = clonebotdb.find()
            cloned_bots_list = await cloned_bots.to_list(length=None)
            total_clones = len(cloned_bots_list)
            await app.send_message(
                int(OWNER_ID),
                f"**#New_Clone**\n\n**Bot:- @{bot.username}**\n\n**Details:-**\n"
                f"{{'bot_id': {bot.id}, 'name': '{bot.first_name}', 'username': '{bot.username}'}}\n\n"
                f"**Total Cloned:-** {total_clones}",
            )
        except Exception:
            logging.warning("Failed to notify OWNER_ID about new clone.")

        # Persist clone details
        try:
            details = {
                "bot_id": bot.id,
                "is_bot": True,
                "user_id": user_id,
                "name": bot.first_name,
                "token": bot_token,
                "username": bot.username,
            }
            await clonebotdb.insert_one(details)
            CLONES.add(bot.id)
        except Exception as e:
            logging.exception("Failed to insert cloned bot into DB.")
            await mi.edit_text("⚠️ Failed to save cloned bot to database. Check logs.")
            # stop temp client before returning
            try:
                await ai.stop()
            except Exception:
                pass
            return

        # Keep the cloned bot client running by leaving it started (ai client continues)
        # Note: ai instance will be garbage-collected if no reference — but because plugin root uses
        # its own lifecycle, you may want to persist a reference somewhere if needed.
        # For simplicity, we stop the temporary client here; restart_bots will pick it up on app start.
        await ai.stop()

        await mi.edit_text(
            f"✅ Bot @{bot.username} has been successfully cloned and saved.\n"
            f"Remove clone by: /delclone bot_token\nCheck all cloned bots by: /cloned"
        )

    except (AccessTokenExpired, AccessTokenInvalid):
        await mi.edit_text("**❌ Invalid or expired bot token. Provide a valid token.**")
        return
    except Exception as e:
        logging.exception("Error during cloning process.")
        # If token already present in DB, tell user; else show generic error
        cloned_bot = await clonebotdb.find_one({"token": bot_token})
        if cloned_bot:
            await mi.edit_text("**🤖 This bot is already cloned.**")
            return

        await mi.edit_text(
            f"⚠️ <b>Error while cloning:</b>\n\n<code>{e}</code>\n\n"
            f"Forward this message to the bot admin for assistance."
        )


# 📋 List cloned bots
@app.on_message(filters.command("cloned"))
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
            text += f"**Bot ID:** `{bot.get('bot_id')}`\n"
            text += f"**Bot Name:** {bot.get('name')}\n"
            username = bot.get("username") or "unknown"
            if username and not username.startswith("@"):
                username = f"@{username}"
            text += f"**Bot Username:** {username}\n\n"
        await message.reply_text(text)
    except Exception as e:
        logging.exception(e)
        await message.reply_text("**An error occurred while listing cloned bots.**")


# ❌ Delete cloned bot by token
@app.on_message(
    filters.command(
        [
            "deletecloned",
            "delcloned",
            "delclone",
            "deleteclone",
            "removeclone",
            "cancelclone",
        ]
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
        ok = await message.reply_text("🔎 Checking the bot token...")

        cloned_bot = await clonebotdb.find_one({"token": bot_token})
        if cloned_bot:
            await clonebotdb.delete_one({"token": bot_token})

            bot_id = cloned_bot.get("bot_id")
            if bot_id in CLONES:
                try:
                    CLONES.remove(bot_id)
                except KeyError:
                    pass

            await ok.edit_text(
                "✅ Your cloned bot has been removed from database.\n"
                "🔒 Revoke the token from @BotFather to fully disable the bot."
            )
        else:
            await ok.edit_text("⚠️ The provided bot token is not in the cloned list.")
    except Exception as e:
        await message.reply_text(f"**An error occurred while deleting the cloned bot:** {e}")
        logging.exception(e)


# ♻️ Restart cloned bots on app restart
async def restart_bots():
    global CLONES
    try:
        logging.info("Restarting all cloned bots...")
        bots = [bot async for bot in clonebotdb.find()]

        async def restart_bot(bot):
            bot_token = bot.get("token")
            if not bot_token:
                logging.warning(f"Skipping bot entry without token: {bot}")
                return

            temp_session_name = f"clone_restart_{bot.get('bot_id')}"
            ai = Client(
                temp_session_name,
                api_id=API_ID,
                api_hash=API_HASH,
                bot_token=bot_token,
                plugins=dict(root="AnanyaxChat/mplugin"),
            )
            try:
                await ai.start()
                bot_info = await ai.get_me()
                try:
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
                except Exception:
                    logging.warning("Failed to set commands on restarted cloned bot.")

                if bot_info.id not in CLONES:
                    CLONES.add(bot_info.id)

            except (AccessTokenExpired, AccessTokenInvalid):
                # Remove expired/invalid tokens from DB
                await clonebotdb.delete_one({"token": bot_token})
                logging.info(f"Removed expired or invalid token for bot ID: {bot.get('bot_id')}")
            except Exception as e:
                logging.exception(f"Error while restarting bot with token {bot_token}: {e}")
            finally:
                try:
                    await ai.stop()
                except Exception:
                    pass

        await asyncio.gather(*(restart_bot(bot) for bot in bots))

    except Exception:
        logging.exception("Error while restarting bots.")


# 🚮 Delete ALL cloned bots (owner only)
@app.on_message(filters.command("delallclone") & filters.user(int(OWNER_ID)))
async def delete_all_cloned_bots(client, message):
    try:
        a = await message.reply_text("**Deleting all cloned bots...**")
        await clonebotdb.delete_many({})
        CLONES.clear()
        await a.edit_text("**All cloned bots have been deleted successfully ✅**")
        # Restart app to ensure cloned instances stop running
        os.system(f"kill -9 {os.getpid()} && bash start")
    except Exception as e:
        await a.edit_text(f"**An error occurred while deleting all cloned bots.** {e}")
        logging.exception(e)
