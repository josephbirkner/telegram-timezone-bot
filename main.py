import logging
from telegram.ext import Updater, MessageHandler, Filters
from datetime import time, datetime
from pytz import all_timezones_set, timezone, utc
import re
from os.path import join, dirname, abspath

with open(join(abspath(dirname(__file__)), "token"), "r") as token_file:
    token = token_file.read()

updater = Updater(token=token, use_context=True)
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

FREEDOM_TIMEZONES = {"edt", "est", "pst", "pdt"}
ALL_TIMEZONES = {tz.lower() for tz in all_timezones_set} | FREEDOM_TIMEZONES

query_re = re.compile(
    f"(?:[^\\d]+|\\d[^\\d])*\\b(\\d{{1,2}})(?::(\\d{{1,2}}))?\\s*(am|pm)?\\s*({'|'.join(ALL_TIMEZONES)})?\\s+(?:(in|to)\\s+)?({'|'.join(ALL_TIMEZONES)})\\b.*"
)


def make_timezone(name: str) -> timezone:
    if name == "edt" or name == "est":
        tz = timezone("US/Eastern")
    elif name == "cest":
        tz = timezone("CET")
    elif name == "pdt" or name == "pst":
        tz = timezone("US/Pacific")
    else:
        tz = timezone(name.upper())
    return tz


def make_time(name: str, hour: int, minute: int) -> datetime:
    now = utc.localize(datetime.now())
    return make_timezone(name).localize(datetime(
        year=now.year,
        month=now.month,
        day=now.day,
        hour=hour,
        minute=minute),
        is_dst=True)


def process_message(update, context):
    msg = update.message.text.lower()
    match = query_re.match(msg)
    if not match:
        return

    try:
        src_hour = int(match.group(1) or "0")
        src_min = int(match.group(2) or "0")
        src_pm = match.group(3)
        src_tz = match.group(4)
        src_separator = match.group(5)
        dest_tz = match.group(6)

        if not src_tz and not src_separator:
            src_tz = dest_tz
            # Default destination timezones
            dest_tz = "cet" if src_tz in FREEDOM_TIMEZONES else "est"
        elif not src_tz:
            src_tz = "cet" if dest_tz in FREEDOM_TIMEZONES else "est"
        if src_pm == "pm":
            src_hour += 12
        orig_time = make_time(src_tz, src_hour, src_min)
        result_time = orig_time.astimezone(make_timezone(dest_tz))
        response = result_time.strftime('%H:%M %Z')
        if response:
            if dest_tz in FREEDOM_TIMEZONES:
                response = f"That's {response} 😜🇺🇸🇺🇸"
            else:
                response = f"That's {response} 🇪🇺👌"
            context.bot.send_message(chat_id=update.effective_chat.id, text=response)
    except Exception as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"Whatevs 😎 ({e})")


message_handler = MessageHandler(Filters.text & (~Filters.command), process_message)
dispatcher.add_handler(message_handler)

updater.start_polling()
updater.idle()
