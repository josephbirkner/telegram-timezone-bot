import logging
import sys

from telegram.ext import Updater, MessageHandler, Filters
from datetime import datetime
from pytz import all_timezones_set, timezone, utc
import re
from os.path import join, dirname, abspath

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

OFFLINE = len(sys.argv) > 1 and sys.argv[1] == "offline"
FREEDOM_TIMEZONES = {"edt", "est", "pst", "pdt"}
ALL_TIMEZONES = {tz.lower() for tz in all_timezones_set} | FREEDOM_TIMEZONES

query_re = re.compile(
    f"(?:[^\\d]+|\\d[^\\d:])*\\b(\\d{{1,2}})(?::(\\d{{1,2}}))?\\s*(am|pm)?\\s*({'|'.join(ALL_TIMEZONES)})?\\s+(?:(in|to)\\s+)?({'|'.join(ALL_TIMEZONES)})\\b.*"
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


def make_response(user_input: str):
    match = query_re.match(user_input)
    if not match:
        return
    try:
        src_hour = int(match.group(1) or "0")
        src_min = int(match.group(2) or "0")
        src_pm = match.group(3)
        src_tz = match.group(4)
        src_separator = match.group(5)
        dest_tz = match.group(6)
        # Default src/dst timezone
        if not src_tz and not src_separator:
            src_tz = dest_tz
            dest_tz = "cet" if src_tz in FREEDOM_TIMEZONES else "est"
        elif not src_tz:
            src_tz = "cet" if dest_tz in FREEDOM_TIMEZONES else "est"
        # AM/PM Conversions
        if src_pm == "pm" and src_hour < 12:
            src_hour += 12
        elif src_pm == "pm" and src_hour == 12:
            src_hour = 0
        orig_time = make_time(src_tz, src_hour, src_min)
        result_time = orig_time.astimezone(make_timezone(dest_tz))
        response = result_time.strftime('%H:%M %Z')
        if response:
            if dest_tz in FREEDOM_TIMEZONES:
                return f"That's {response} 😜🇺🇸🇺🇸"
            else:
                return f"That's {response} 🇪🇺👌"
    except Exception as e:
        return f"Whatevs 😎 ({e})"


if not OFFLINE:

    def process_message(update, context):
        msg = update.message.text.lower()
        response = make_response(msg)
        if response:
            context.bot.send_message(chat_id=update.effective_chat.id, text=response)

    with open(join(abspath(dirname(__file__)), "token"), "r") as token_file:
        token = token_file.read()
    updater = Updater(token=token, use_context=True)
    message_handler = MessageHandler(Filters.text & (~Filters.command), process_message)
    updater.dispatcher.add_handler(message_handler)
    updater.start_polling()
    updater.idle()

else:

    user_input_text = ""
    while True:
        user_input_text = input().lower()
        if user_input_text in {"q", "exit", "quit"}:
            break
        print(f"> {make_response(user_input_text)}")
