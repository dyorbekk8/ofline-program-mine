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

# Logging sozlamalari (Railway logs orqali kuzatish uchun)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("OutreachBot")

# Muhit o'zgaruvchilarini yuklash
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
      "Outreach bot ishga tushdi va Google Sheets bilan ishlamoqda..."
  )

  while True:
    try:
      # 1. Google Sheets "Config" sahifasidan holatni o'qiymiz
      config = get_config("LeadsBot")
      today = datetime.now().strftime("%Y-%m-%d")

      last_run_date = config.get("last_run_date", "")
      discord_extra = int(config.get("discord_extra", 0))
      x_extra = int(config.get("x_extra", 0))

      # Agar yangi kun boshlangan bo'lsa, limitlarni oshiramiz va Config'ni yangilaymiz
      if last_run_date != today:
        if last_run_date != "":
          discord_extra += 1
          x_extra += 1
          update_config("discord_extra", str(discord_extra), "LeadsBot")
          update_config("x_extra", str(x_extra), "LeadsBot")
          logger.info(
              "Yangi kun! Limitlar yangilandi: Discord extra:"
              f" {discord_extra}, X extra: {x_extra}"
          )
        update_config("last_run_date", today, "LeadsBot")

      # Dinamik limitlar
      discord_limit = 12 + discord_extra
      x_limit = 17 + x_extra

      logger.info(f"Kunlik limitlar yuklandi. Leads o'qilmoqda...")

      # 2. Google Sheets "Leads" sahifasidan faqat "Pending" statusdagilarni olamiz
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

        # Shablon tanlash va ism-kompaniyani joylash
        template_id = random.randint(0, len(OUTREACH_TEMPLATES) - 1)
        template = OUTREACH_TEMPLATES[template_id]
        sample_message = template.format(name=name, company=company)

        success = False

        # Platformaga qarab yuborish
        if platform == "instagram" and IG_SESSION_ID:
          await send_instagram_dm(target, sample_message)
          success = True
        elif platform == "facebook" and FB_C_USER and FB_XS:
          await send_facebook_dm(target, sample_message)
          success = True
        elif platform == "discord" and DISCORD_USER_TOKEN:
          await send_discord_dm(target, sample_message)
          success = True
        elif platform == "telegram":
          # Qaysi Telegram sessiya bo'shligiga qarab
          if TG_SESSION_1:
            await send_telegram_dm(TG_SESSION_1, target, sample_message)
            success = True
          elif TG_SESSION_2:
            await send_telegram_dm(TG_SESSION_2, target, sample_message)
            success = True
        elif platform == "x" or platform == "twitter" and X_AUTH_TOKEN:
          await send_x_dm(target, sample_message)
          success = True

        if success:
          # 3. Xabar ketgach jadvalni yangilaymiz (Status: Sent, Template ID va vaqt)
          update_lead_status(
              row_index,
              status="Sent",
              template_id=template_id + 1,
              sheet_name="LeadsBot",
          )
          logger.info(
              f"Lid yuborildi va jadval yangilandi: {target} ({platform})"
          )
          await safe_delay()
        else:
          logger.warning(
              f"Platforma topilmadi yoki token xato: {platform} -> {target}"
          )

    except Exception as e:
      logger.error(f"Xatolik yuz berdi: {e}")
      await asyncio.sleep(60)


if __name__ == "__main__":
  try:
    asyncio.run(outreach_loop())
  except KeyboardInterrupt:
    logger.info("Bot foydalanuvchi tomonidan to'xtatildi.")
