import re
from pyrogram import filters, Client
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, UsernameInvalid, UsernameNotModified
from info import ADMINS, LOG_CHANNEL, FILE_STORE_CHANNEL
from database.ia_filterdb import unpack_new_file_id
from utils import temp
import re
import os
import json
import base64
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@Client.on_message(filters.command('links') & filters.user(ADMINS))
async def gen_link_s(bot, message):
    replied = message.reply_to_message
    if not replied:
        return await message.reply('R͟e͟p͟l͟y͟ t͟o͟ a͟ m͟e͟s͟s͟a͟g͟e͟ t͟o͟ g͟e͟t͟ a͟ s͟h͟a͟r͟e͟a͟b͟l͟e͟ l͟i͟n͟k͟.')
    file_type = replied.media
    if file_type not in ["video", 'audio', 'document', 'sticker', 'photo']:
        return await message.reply("Reply to a supported media")
    file_id, ref = unpack_new_file_id((getattr(replied, file_type)).file_id)
    await message.reply(f"Here is your Link:\nhttps://t.me/{temp.U_NAME}?start={file_id}")
    
    
@Client.on_message(filters.command('batch') & filters.user(ADMINS))
async def gen_link_batch(bot, message):
    if " " not in message.text:
        return await message.reply("Use correct format.\nExample <code>/batch https://t.me/TeamEvamaria/10 https://t.me/TeamEvamaria/20</code>.")
    links = message.text.strip().split(" ")
    if len(links) != 3:
        return await message.reply("Use correct format.\nExample <code>/batch https://t.me/TeamEvamaria/10 https://t.me/TeamEvamaria/20</code>.")
    _, first, last = links
    regex = re.compile("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
    match = regex.match(first)
    if not match:
        return await message.reply('Invalid link')
    f_chat_id = match.group(4)
    f_msg_id = int(match.group(5))
    if f_chat_id.isnumeric():
        f_chat_id  = int(("-100" + f_chat_id))

    match = regex.match(last)
    if not match:
        return await message.reply('Invalid link')
    l_chat_id = match.group(4)
    l_msg_id = int(match.group(5))
    if l_chat_id.isnumeric():
        l_chat_id  = int(("-100" + l_chat_id))

    if f_chat_id != l_chat_id:
        return await message.reply("Chat ids not matched.")
    try:
        chat_id = (await bot.get_chat(f_chat_id)).id
    except ChannelInvalid:
        return await message.reply('This may be a private channel / group. Make me an admin over there to index the files.')
    except (UsernameInvalid, UsernameNotModified):
        return await message.reply('Invalid Link specified.')
    except Exception as e:
        return await message.reply(f'Errors - {e}')

    sts = await message.reply("G͟e͟n͟e͟r͟a͟t͟i͟n͟g͟ l͟i͟n͟k͟ f͟o͟r͟ y͟o͟u͟r͟ m͟e͟s͟s͟a͟g͟e͟.\nT͟h͟i͟s͟ m͟a͟y͟ t͟a͟k͟e͟ t͟i͟m͟e͟ d͟e͟p͟e͟n͟d͟i͟n͟g͟ u͟p͟o͟n͟ n͟u͟m͟b͟e͟r͟ o͟f͟ m͟e͟s͟s͟a͟g͟e͟s͟")
    if chat_id in FILE_STORE_CHANNEL:
        string = f"{f_msg_id}_{l_msg_id}_{chat_id}"
        b_64 = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
        return await sts.edit(f"Here is your link https://t.me/{temp.U_NAME}?start=DSTORE-{b_64}")
 
    FRMT = "G͟e͟n͟e͟r͟a͟t͟i͟n͟g͟ l͟i͟n͟k͟ f͟o͟r͟ y͟o͟u͟r͟ m͟e͟s͟s͟a͟g͟e͟...\nTotal Messages: `{total}`\nDone: `{current}`\nRemaining: `{rem}`\nStatus: `{sts}`"

    outlist = []
    
    # file store without db channel
    og_msg = 0
    tot = 0
    async for msg in bot.iter_messages(f_chat_id, l_msg_id, f_msg_id):
        tot += 1
        if msg.empty or msg.service:
            continue
        if not msg.media:
            # only media messages supported.
            continue
        try:
            file_type = msg.media
            file = getattr(msg, file_type)
            caption = getattr(msg, 'caption', '')
            if caption:
                caption = caption.html
            if file:
                file = {
                    "file_id": file.file_id,
                    "caption": caption,
                    "title": getattr(file, "file_name", ""),
                    "size": file.file_size,
                }
                og_msg +=1
                outlist.append(file)
        except:
            pass
        if not og_msg % 20:
            try:
                await sts.edit(FRMT.format(total=l_msg_id-f_msg_id, current=tot, rem=((l_msg_id-f_msg_id) - tot), sts="Saving Messages"))
            except:
                pass
    with open(f"batchmode_{message.from_user.id}.json", "w+") as out:
        json.dump(outlist, out)
    post = await bot.send_document(LOG_CHANNEL, f"batchmode_{message.from_user.id}.json", file_name="Batch.json", caption="⚠️Generated for filestore.")
    os.remove(f"batchmode_{message.from_user.id}.json")
    file_id, ref = unpack_new_file_id(post.document.file_id)
    await sts.edit(f"Here is your link\nContains `{og_msg}` files.\n https://t.me/{temp.U_NAME}?start=BATCH-{file_id}")