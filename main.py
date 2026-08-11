import asyncio
from datetime import datetime
import logging
import os
import random
from sheets import (
    get_config,
    get_pending_leads,
    update_config,
    update_lead_status,
)
from templates import OUTREACH_TEMPLATES

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("OutreachBot")

# Muhit o'zgaruvchilari
TG_SESSION_1 = os.getenv("TG_SESSION_1")
TG_SESSION_2 = os.getenv("TG_SESSION_2")
DISCORD_USER_TOKEN = os.getenv("DISCORD_USER_TOKEN")
X_AUTH_TOKEN = os.getenv("X_AUTH_TOKEN")
IG_SESSION_ID = os.getenv("IG_SESSION_ID")
FB_C_USER = os.getenv("FB_C_USER")
FB_XS = os.getenv("FB_XS")


async def send_instagram_dm(target, message):
  logger.info(f"[Instagram] Xabar yuborildi -> {target}")
  await asyncio.sleep(1)


async def send_facebook_dm(target, message):
  logger.info(f"[Facebook] Xabar yuborildi -> {target}")
  await asyncio.sleep(1)


async def send_discord_dm(target, message):
  logger.info(f"[Discord] Xabar yuborildi -> {target}")
  await asyncio.sleep(1)


async def send_telegram_dm(session_id, target, message):
  logger.info(f"[Telegram Session] Xabar yuborildi -> {target}")
  await asyncio.sleep(1)


async def send_x_dm(target, message):
  logger.info(f"[X / Twitter] Xabar yuborildi -> {target}")
  await asyncio.sleep(1)


async def safe_delay():
  delay_seconds = random.randint(2400, 4200)
  delay_minutes = delay_seconds // 60
  logger.info(
      f"Xavfsizlik uchun {delay_minutes} daqiqa ( {delay_seconds} soniya ) pauza"
      " boshlandi..."
  )
  await asyncio.sleep(delay_seconds)


async def outreach_loop():
  logger.info(
      "Outreach bot ishga tushdi va real vaqt limitlarini nazorat qilmoqda..."
  )

  while True:
    try:
      config = get_config("LeadsBot")
      today = datetime.now().strftime("%Y-%m-%d")

      last_run_date = config.get("last_run_date", "")

      # Real vaqt bo'yicha yangi kun boshlansa, hisoblagichlarni 0 ga tushiramiz
      if last_run_date != today:
        update_config("last_run_date", today, "LeadsBot")
        update_config("ig_sent", "0", "LeadsBot")
        update_config("fb_sent", "0", "LeadsBot")
        update_config("discord_sent", "0", "LeadsBot")
        update_config("tg1_sent", "0", "LeadsBot")
        update_config("tg2_sent", "0", "LeadsBot")
        update_config("x_sent", "0", "LeadsBot")

        config = get_config("LeadsBot")
        logger.info(
            "Yangi kun! Barcha kunlik hisoblagichlar 0 dan boshlandi."
        )

      # Joriy yuborilganlar soni
      ig_sent = int(config.get("ig_sent", 0))
      fb_sent = int(config.get("fb_sent", 0))
      discord_sent = int(config.get("discord_sent", 0))
      tg1_sent = int(config.get("tg1_sent", 0))
      tg2_sent = int(config.get("tg2_sent", 0))
      x_sent = int(config.get("x_sent", 0))

      # Qat'iy kunlik limitlar
      IG_LIMIT = 10
      FB_LIMIT = 10
      DISCORD_LIMIT = 12
      TG_LIMIT = 5
      X_LIMIT = 17

      pending_leads = get_pending_leads("LeadsBot")

      if not pending_leads:
        logger.info("Yangi 'Pending' lidlar topilmadi. 10 daqiqa kutamiz...")
        await asyncio.sleep(600)
        continue

      for lead in pending_leads:
        row_index = lead["row_index"]
        platform = str(lead["Platform"]).strip().lower()
        target = lead["Target"]
        name = lead["Name"]
        company = lead["Company"]

        template_id = random.randint(0, len(OUTREACH_TEMPLATES) - 1)
        template = OUTREACH_TEMPLATES[template_id]
        sample_message = template.format(name=name, company=company)

        success = False
        sent_key = None

        if platform == "instagram" and IG_SESSION_ID:
          if ig_sent < IG_LIMIT:
            await send_instagram_dm(target, sample_message)
            success = True
            ig_sent += 1
            sent_key = "ig_sent"
          else:
            logger.warning("Instagram uchun kunlik limit tugadi!")

        elif platform == "facebook" and FB_C_USER and FB_XS:
          if fb_sent < FB_LIMIT:
            await send_facebook_dm(target, sample_message)
            success = True
            fb_sent += 1
            sent_key = "fb_sent"
          else:
            logger.warning("Facebook uchun kunlik limit tugadi!")

        elif platform == "discord" and DISCORD_USER_TOKEN:
          if discord_sent < DISCORD_LIMIT:
            await send_discord_dm(target, sample_message)
            success = True
            discord_sent += 1
            sent_key = "discord_sent"
          else:
            logger.warning("Discord uchun kunlik limit tugadi!")

        elif platform == "telegram":
          if tg1_sent < TG_LIMIT and TG_SESSION_1:
            await send_telegram_dm(TG_SESSION_1, target, sample_message)
            success = True
            tg1_sent += 1
            sent_key = "tg1_sent"
          elif tg2_sent < TG_LIMIT and TG_SESSION_2:
            await send_telegram_dm(TG_SESSION_2, target, sample_message)
            success = True
            tg2_sent += 1
            sent_key = "tg2_sent"
          else:
            logger.warning("Telegram akkauntlarining limiti tugadi!")

        elif (platform == "x" or platform == "twitter") and X_AUTH_TOKEN:
          if x_sent < X_LIMIT:
            await send_x_dm(target, sample_message)
            success = True
            x_sent += 1
            sent_key = "x_sent"
          else:
            logger.warning("X (Twitter) uchun kunlik limit tugadi!")

        if success and sent_key:
          update_lead_status(
              row_index,
              status="Sent",
              template_id=template_id + 1,
              sheet_name="LeadsBot",
          )
          update_config(sent_key, str(locals()[sent_key]), "LeadsBot")
          logger.info(
              f"Lid yuborildi va limit yangilandi: {target} ({platform})"
          )
          await safe_delay()
        else:
          logger.warning(
              f"Xabar yuborilmadi (Limit tugagan yoki platforma xato):"
              f" {platform} -> {target}"
          )

    except Exception as e:
      logger.error(f"Xatolik yuz berdi: {e}")
      await asyncio.sleep(60)


if __name__ == "__main__":
  try:
    asyncio.run(outreach_loop())
  except KeyboardInterrupt:
    logger.info("Bot foydalanuvchi tomonidan to'xtatildi.")
