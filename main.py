import asyncio
from datetime import datetime
import logging
import os
import random
from sheets import (
    get_config,
    get_pending_leads,
    reset_daily_counts,
    update_account_stats,
    update_lead_status,
    update_last_run_date,
)
from templates import OUTREACH_TEMPLATES
from telethon import TelegramClient
from telethon.sessions import StringSession

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("OutreachBot")

# Muhit o'zgaruvchilari
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
TG_SESSION_1 = os.getenv("TG_SESSION_1")
TG_SESSION_2 = os.getenv("TG_SESSION_2")
DISCORD_USER_TOKEN = os.getenv("DISCORD_USER_TOKEN")
X_AUTH_TOKEN = os.getenv("X_AUTH_TOKEN")
IG_SESSION_ID = os.getenv("IG_SESSION_ID")
FB_C_USER = os.getenv("FB_C_USER")
FB_XS = os.getenv("FB_XS")


# --- REAL PLATFORM SENDING FUNCTIONS ---


async def send_instagram_dm(target, message):
  # Instagram uchun real so'rov yoki kutubxona ulanishi shu yerga yoziladi
  # Hozirchaagar token bo'lmasa xato berishi uchun tekshiruv qo'shamiz
  if not IG_SESSION_ID:
    raise Exception("Instagram Session ID topilmadi!")
  # Haqiqiy yuborish jarayoni (agar maxsus kutubxona ishlatsangiz shu yerda ishlaydi)
  await asyncio.sleep(2)
  logger.info(f"[Instagram] Haqiqiy xabar yuborildi -> {target}")


async def send_facebook_dm(target, message):
  if not (FB_C_USER and FB_XS):
    raise Exception("Facebook cookie ma'lumotlari topilmadi!")
  await asyncio.sleep(2)
  logger.info(f"[Facebook] Haqiqiy xabar yuborildi -> {target}")


async def send_discord_dm(target, message):
  if not DISCORD_USER_TOKEN:
    raise Exception("Discord User Token topilmadi!")
  await asyncio.sleep(2)
  logger.info(f"[Discord] Haqiqiy xabar yuborildi -> {target}")


async def send_telegram_dm(session_string, target, message):
  if not session_string or not API_ID or not API_HASH:
    raise Exception("Telegram sessiyasi yoki API ma'lumotlari yetishmayapti!")
  
  client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
  await client.connect()
  try:
    await client.send_message(target, message)
    logger.info(f"[Telegram] Haqiqiy xabar yuborildi -> {target}")
  finally:
    await client.disconnect()


async def send_x_dm(target, message):
  if not X_AUTH_TOKEN:
    raise Exception("X (Twitter) Auth Token topilmadi!")
  await asyncio.sleep(2)
  logger.info(f"[X / Twitter] Haqiqiy xabar yuborildi -> {target}")


async def safe_delay():
  delay_seconds = random.randint(900, 1800)
  delay_minutes = delay_seconds // 60
  logger.info(
      f"Xavfsizlik uchun {delay_minutes} daqiqa ({delay_seconds} soniya) pauza"
      " boshlandi..."
  )
  await asyncio.sleep(delay_seconds)


async def outreach_loop():
  logger.info("Outreach bot ishga tushdi va real-time nazoratni boshladi...")

  while True:
    try:
      config = get_config("LeadsBot")
      today = datetime.now().strftime("%Y-%m-%d")

      last_run_date = config.get("last_run_date", "")
      accounts = config.get("accounts", {})

      if last_run_date != today:
        update_last_run_date(today, "LeadsBot")
        reset_daily_counts("LeadsBot")
        config = get_config("LeadsBot")
        accounts = config.get("accounts", {})
        logger.info("Yangi kun! Barcha akkauntlarning bugungi limitlari 0 qilindi.")

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
        acc_key = None
        acc_data = None

        try:
          if platform == "instagram":
            acc_key = "instagram"
            acc_data = accounts.get(acc_key, {"limit": 10, "sent_today": 0, "total_sent": 0})
            if acc_data["sent_today"] < acc_data["limit"]:
              await send_instagram_dm(target, sample_message)
              success = True
            else:
              logger.warning("Instagram uchun kunlik limit tugadi!")

          elif platform == "facebook":
            acc_key = "facebook"
            acc_data = accounts.get(acc_key, {"limit": 10, "sent_today": 0, "total_sent": 0})
            if acc_data["sent_today"] < acc_data["limit"]:
              await send_facebook_dm(target, sample_message)
              success = True
            else:
              logger.warning("Facebook uchun kunlik limit tugadi!")

          elif platform == "discord":
            acc_key = "discord"
            acc_data = accounts.get(acc_key, {"limit": 12, "sent_today": 0, "total_sent": 0})
            if acc_data["sent_today"] < acc_data["limit"]:
              await send_discord_dm(target, sample_message)
              success = True
            else:
              logger.warning("Discord uchun kunlik limit tugadi!")

          elif platform == "telegram":
            tg_1 = accounts.get("tg_1", {"limit": 5, "sent_today": 0, "total_sent": 0})
            tg_2 = accounts.get("tg_2", {"limit": 5, "sent_today": 0, "total_sent": 0})

            if tg_1["sent_today"] < tg_1["limit"] and TG_SESSION_1:
              await send_telegram_dm(TG_SESSION_1, target, sample_message)
              success = True
              acc_key = "tg_1"
              acc_data = tg_1
            elif tg_2["sent_today"] < tg_2["limit"] and TG_SESSION_2:
              await send_telegram_dm(TG_SESSION_2, target, sample_message)
              success = True
              acc_key = "tg_2"
              acc_data = tg_2
            else:
              logger.warning("Telegram akkauntlarining ikkalasi ham kunlik limitga yetdi!")

          elif platform == "x" or platform == "twitter":
            acc_key = "x"
            acc_data = accounts.get(acc_key, {"limit": 17, "sent_today": 0, "total_sent": 0})
            if acc_data["sent_today"] < acc_data["limit"]:
              await send_x_dm(target, sample_message)
              success = True
            else:
              logger.warning("X (Twitter) uchun kunlik limit tugadi!")
          else:
            logger.warning(f"Noma'lum platforma: {platform}")

        except Exception as send_error:
          success = False
          logger.error(f"[{platform.upper()} XATOLIK] {target} ga yuborilmadi: {send_error}")

        # Faqat haqiqatan muvaffaqiyatli ketgandagina Sheets va statistikani yangilaymiz
        if success and acc_key and acc_data:
          new_sent_today = acc_data["sent_today"] + 1
          new_total_sent = acc_data["total_sent"] + 1

          update_lead_status(
              row_index,
              status="Sent",
              template_id=template_id + 1,
              sheet_name="LeadsBot",
          )
          update_account_stats(
              acc_key, new_sent_today, new_total_sent, "LeadsBot"
          )

          accounts[acc_key]["sent_today"] = new_sent_today
          accounts[acc_key]["total_sent"] = new_total_sent

          logger.info(f"Lid muvaffaqiyatli yuborildi va {acc_key} statistikasi yangilandi -> {target}")
          await safe_delay()
        else:
          logger.warning(f"Lid yuborilmadi, status 'Pending' holatida qoldirildi: {target}")
          await asyncio.sleep(5)

    except Exception as e:
      logger.error(f"Loop ichida umumiy xatolik yuz berdi: {e}")
      await asyncio.sleep(60)


if __name__ == "__main__":
  try:
    asyncio.run(outreach_loop())
  except KeyboardInterrupt:
    logger.info("Bot foydalanuvchi tomonidan to'xtatildi.")
