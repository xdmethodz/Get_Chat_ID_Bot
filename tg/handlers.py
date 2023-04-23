from pyrogram import Client, filters, types, handlers
from pyrogram.raw.types import (KeyboardButtonRequestPeer, RequestPeerTypeUser, ReplyKeyboardMarkup,
                                KeyboardButtonRow, UpdateNewMessage, RequestPeerTypeChat,
                                RequestPeerTypeBroadcast, PeerChat, PeerChannel)
from pyrogram.raw.functions.messages import SendMessage
from pyrogram.types import User, Chat

from tg import filters as tg_filters
from db import filters as db_filters


async def start(c: Client, msg: types.Message):
    name = msg.from_user.first_name + \
           (" " + last if (last := msg.from_user.last_name) else "")
    text2 = "בבוט זה תוכל לקבל id של קבוצה ערוץ או משתמש"
    text = f"ברוך הבא {name}\n\n{text2}\n\n" \
           f"בשביל להשתמש בבוט אנא לחצו על הכפתורים למטה ושתפו את הערוץ הקבוצה או המשתמש."
    peer = await c.resolve_peer(msg.chat.id)
    await c.invoke(
        SendMessage(peer=peer, message=text, random_id=c.rnd_id(),
                    reply_markup=ReplyKeyboardMarkup(rows=[
                        KeyboardButtonRow(
                            buttons=[
                                KeyboardButtonRequestPeer(text='משתמש',
                                                          button_id=1,
                                                          peer_type=RequestPeerTypeUser()),
                                KeyboardButtonRequestPeer(text='קבוצה',
                                                          button_id=2,
                                                          peer_type=RequestPeerTypeChat()),
                                KeyboardButtonRequestPeer(text='ערוץ',
                                                          button_id=3,
                                                          peer_type=RequestPeerTypeBroadcast())
                            ]
                        )

                    ], resize=True))
    )


def get_stats(c: Client, msg: types.Message):
    msg.reply(f'כמות המשתמשים בבוט היא: {db_filters.get_tg_count()}')


def forward(_, msg: types.Message):
    if isinstance(msg.forward_from, User):
        # user
        text = f"ה ID הוא: `{msg.forward_from.id}`"
    elif isinstance(msg.forward_from_chat, Chat):
        # channel
        text = f"ה ID הוא: \u200e`{msg.forward_from_chat.id}`"
    elif msg.forward_sender_name:
        # The user hides the forwarding of a message from him or Deleted Account
        text = f'ה ID מוסתר\n{msg.forward_sender_name}'
    else:
        return
    msg.reply(text=text)


async def raw(c: Client, update: UpdateNewMessage, users, chats):
    try:
        if update.message.action.button_id:
            button_id = update.message.action.button_id
            chat = update.message.action.peer
            if button_id == 1:
                # print("user")
                text = f"ה ID הוא: `{chat.user_id}`"
            elif button_id == 2:
                if isinstance(chat, PeerChat):
                    # print('group')
                    text = f"ה ID הוא: `{chat.chat_id}`"
                elif isinstance(chat, PeerChannel):
                    # print('super group')
                    text = f"ה ID הוא: `\u200e-100{chat.channel_id}`"
                else:
                    return
            else:
                # print("channel")
                text = f"ה ID הוא: `\u200e-100{chat.channel_id}`"
        else:
            return
        await c.send_message(chat_id=update.message.peer_id.user_id,
                             reply_to_message_id=update.message.id, text=text)
        return
    except AttributeError:
        return


HANDLERS = [
    handlers.MessageHandler(start, filters.text & filters.command("start")
                            & filters.private & filters.create(tg_filters.create_user)),
    handlers.MessageHandler(forward, filters.forwarded & filters.private
                            & filters.create(tg_filters.create_user)),
    handlers.MessageHandler(get_stats, filters.text & filters.command("stats")
                            & filters.private & filters.create(tg_filters.create_user)
                            & filters.create(tg_filters.is_admin)),
    handlers.RawUpdateHandler(raw)
]