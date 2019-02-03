#!/usr/bin/env python3
from telegram import Bot, InputMediaPhoto
import json
import logging
import os
import sys
from updatedb import MeshUpdater, SafeGet
from PIL import Image, ImageEnhance
from io import BytesIO
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

cwd = os.path.dirname(os.path.abspath(__file__))


def load_tokens():
    try:
        with open(os.path.join(cwd, 'tokens.json'), 'r') as fp:
            tokens = json.load(fp)
            bot_token = tokens['bot_token']
            users_ids = tokens['users_id']
    except FileNotFoundError:
        print("""
            Create a tokens.json file with:
            -bot_token        string
            -users_id         list of strings
            """)
        sys.exit()
    except KeyError:
        print("""
            tokens.json lacks something between:
            -bot_token        string
            -users_id         list of strings
            """)
        sys.exit()
    return bot_token, users_ids


def paste_not_avail(image):
    """
    Add not_available.png overlay to image, centered.
    """
    na = Image.open(os.path.join(cwd, 'not_available.png'))
    na_width, na_height = na.size
    im_width, im_height = image.size
    offset_width = (im_width - na_width) // 2
    offset_height = (im_height - na_height) // 2
    image.paste(na, (offset_width, offset_height), na)
    return image


def desaturate(image):
    return ImageEnhance.Color(image).enhance(0.25)


def filtered_media(url, caption, img_filter):
    """
    Fetch image from url, apply provided img_filter and return
    Python Telegram Bot compatible InputMediaPhoto with provided caption.
    """
    r = SafeGet.get(url)
    img = Image.open(BytesIO(r.content))
    img = img_filter(img)
    bio = BytesIO()
    bio.name = 'temp.jpeg'
    img.save(bio, 'JPEG')
    bio.seek(0)
    return InputMediaPhoto(bio, caption=caption)


def send_album(bot, chat_ids, items, caption_pattern, img_filter=None):
    """
    Send items images as an album to every id in chat_ids and
    eventually apply custom img_filter.
    caption_pattern should follow Python format syntax, with one placeholder.
    """
    if img_filter is None:
        medias = [InputMediaPhoto(i['img_src'],
                  caption=caption_pattern.format(i['name'])) for i in items]
    else:
        medias = [filtered_media(
                    i['img_src'],
                    img_filter=img_filter,
                    caption=caption_pattern.format(i['name'])) for i in items]
    for chat in chat_ids:
        bot.sendMediaGroup(chat_id=chat, media=medias, timeout=30)


def announce_new(bot, chat_ids, items):
    if items == []:
        logging.info("Nothing new")
        return
    for item in items:
        logging.info("New item:\n"+json.dumps(item, indent=3))
    while len(items) > 0:
        temp = items[:10]
        items = items[10:]
        send_album(bot, chat_ids, temp,
                   caption_pattern="{} is now available")


def announce_removed(bot, chat_ids, items):
    if items == []:
        logging.info("Nothing removed")
        return
    for item in items:
        logging.info("Removed item:\n"+json.dumps(item, indent=3))
    while len(items) > 0:
        temp = items[:10]
        items = items[10:]
        send_album(bot, chat_ids, temp,
                   caption_pattern="{} isn't available anymore",
                   img_filter=paste_not_avail)


def main(mesh_id=671):
    updater = MeshUpdater(mesh_id=mesh_id)
    changes = updater.run()
    tokens = load_tokens()
    bot = Bot(tokens[0])
    chats = tokens[1]
    announce_new(bot, chats, changes['new'])
    announce_removed(bot, chats, changes['removed'])


if __name__ == "__main__":
    main()
