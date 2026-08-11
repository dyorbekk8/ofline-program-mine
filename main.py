import asyncio
from datetime import datetime
import json
import logging
import os
import random
from templates import OUTREACH_TEMPLATES

# Logging sozlamalari (Railway logs orqali kuzatish uchun)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("OutreachBot")

# State fayli (Discord va X uchun har kunlik limitni +1 oshirib borishni saqlash uchun)
STATE_FILE = "bot_state.json"


def load_state():
  if os.path.exists(STATE_FILE):
    try:
      with open(STATE_FILE, "r") as f:
        return json.load(f)
    except Exception:
      pass
  return {
      "start_date": datetime.now().strftime("%Y-%m-%d"),
      "discord_extra": 0,
      "x_extra": 0,
      "last_run_date": "",
  }


def save_state(state):
  with open(STATE_FILE, "w") as f:
    json.dump(state, f)


# Muhit o'zgaruvchilarini yuklash
TG_SESSION_1 = os.getenv("TG_SESSION_1")
TG_SESSION_2 = os.getenv("TG_SESSION_2")
DISCORD_USER_TOKEN = os.getenv("DISCORD_USER_TOKEN")
X_AUTH_TOKEN = os.getenv("X_AUTH_TOKEN")
IG_SESSION_ID = os.getenv("IG_SESSION_ID")
FB_C_USER = os.getenv("FB_C_USER")
FB_XS = os.getenv("FB_XS")


async def send_instagram_dm(target, message):
  # Instagram orqali xabar yuborish mantiqi (instagrapi yoki requests)
  logger.info(f"[Instagram] Xabar yuborildi -> {target}")
  await asyncio.sleep(1)


async def send_facebook_dm(target, message):
  # Facebook orqali xabar yuborish mantiqi
  logger.info(f"[Facebook] Xabar yuborildi -> {target}")
  await asyncio.sleep(1)


async def send_discord_dm(target, message):
  # Discord orqali xabar yuborish mantiqi
  logger.info(f"[Discord] Xabar yuborildi -> {target}")
  await asyncio.sleep(1)


async def send_telegram_dm(session_id, target, message):
  # Telegram orqali xabar yuborish mantiqi (Telethon / Pyrogram)
  logger.info(f"[Telegram Session] Xabar yuborildi -> {target}")
  await asyncio.sleep(1)


async def send_x_dm(target, message):
  # X (Twitter) orqali xabar yuborish mantiqi
  logger.info(f"[X / Twitter] Xabar yuborildi -> {target}")
  await asyncio.sleep(1)


async def safe_delay():
  # 40 dan 70 daqiqagacha tasodifiy pauza (soniyalarda: 2400 - 4200 sekund)
  delay_seconds = random.randint(2400, 4200)
  delay_minutes = delay_seconds // 60
  logger.info(
      f"Xavfsizlik uchun {delay_minutes} daqiqa ( {delay_seconds} soniya ) pauza"
      " boshlandi..."
  )
  await asyncio.sleep(delay_seconds)


async def outreach_loop():
  logger.info("Outreach bot ishga tushdi va tarmoqlarni boshqarmoqda...")

  while True:
    state = load_state()
    today = datetime.now().strftime("%Y-%m-%d")

    # Agar yangi kun boshlangan bo'lsa, Discord va X limitlarini +1 ga oshiramiz
    if state["last_run_date"] != today:
      if state["last_run_date"] != "":
        state["discord_extra"] += 1
        state["x_extra"] += 1
        logger.info(
            "Yangi kun! Limitlar yangilandi: Discord extra:"
            f" {state['discord_extra']}, X extra: {state['x_extra']}"
        )
      state["last_run_date"] = today
      save_state(state)

    # Dinamik limitlar
    ig_limit = 10
    fb_limit = 10
    discord_limit = 12 + state["discord_extra"]
    tg_limit_per_acc = 5
    x_limit = 17 + state["x_extra"]

    logger.info(
        f"Bugungi limitlar - IG: {ig_limit}, FB: {fb_limit}, Discord:"
        f" {discord_limit}, TG (har biri): {tg_limit_per_acc}, X: {x_limit}"
    )

    # Misol tariqasida bazadan yoki ro'yxatdan olingan targetlar (leids)
    # Bu yerda o'zingizning lead qidirish funksiyangiz yoki bazangiz ulanadi.

    # Tasodifiy matn tanlash namuna:
    template = random.choice(OUTREACH_TEMPLATES)
    sample_message = template.format(name="Founder", company="CryptoProject")

    # Misol uchun Instagram orqali bitta xabar yuborish jarayoni
    if IG_SESSION_ID:
      await send_instagram_dm("sample_insta_target", sample_message)
      await safe_delay()

    # Facebook orqali xabar yuborish jarayoni
    if FB_C_USER and FB_XS:
      await send_facebook_dm("sample_fb_target", sample_message)
      await safe_delay()

    # Discord orqali xabar yuborish jarayoni
    if DISCORD_USER_TOKEN:
      await send_discord_dm("sample_discord_target", sample_message)
      await safe_delay()

    # Telegram 1-raqam orqali
    if TG_SESSION_1:
      await send_telegram_dm(
          TG_SESSION_1, "sample_tg_target_1", sample_message
      )
      await safe_delay()

    # Telegram 2-raqam orqali
    if TG_SESSION_2:
      await send_telegram_dm(
          TG_SESSION_2, "sample_tg_target_2", sample_message
      )
      await safe_delay()

    # X (Twitter) orqali
    if X_AUTH_TOKEN:
      await send_x_dm("sample_x_target", sample_message)
      await safe_delay()

    logger.info(
        "Barcha tarmoqlar bo'yicha sikl yakunlandi. Navbatdagi sikl kutilmoqda..."
    )


if __name__ == "__main__":
  try:
    asyncio.run(outreach_loop())
  except KeyboardInterrupt:
    logger.info("Bot foydalanuvchi tomonidan to'xtatildi.")
