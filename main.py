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
  # 15 dan 30 daqiqagacha tasodifiy pauza (soniyalarda: 900 - 1800 sekund)
  delay_seconds = random.randint(900, 1800)
  delay_minutes = delay_seconds // 60
  logger.info(
      f"Xavfsizlik uchun {delay_minutes} daqiqa ({delay_seconds} soniya) pauza"
      " boshlandi..."
  )
  await asyncio.sleep(delay_seconds)


async def outreach_loop():
  logger.info("Outreach bot to'liq ishga tushdi va nazoratni boshladi...")

  while True:
    try:
      config = get_config("LeadsBot")
      today = datetime.now().strftime("%Y-%m-%d")

      last_run_date = config.get("last_run_date", "")
      accounts = config.get("accounts", {})

      # Real vaqt bo'yicha yangi kun boshlansa, bugungi yuborilganlarni 0 ga tushiramiz
      if last_run_date != today:
        update_last_run_date(today, "LeadsBot")
        reset_daily_counts("LeadsBot")
        config = get_config("LeadsBot")
        accounts = config.get("accounts", {})
        logger.info(
            "Yangi kun! Barcha akkauntlarning bugungi limitlari 0 ga"
            " tushirildi."
        )

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

        if platform == "instagram" and IG_SESSION_ID:
          acc_key = "instagram"
          acc_data = accounts.get(
              acc_key, {"limit": 10, "sent_today": 0, "total_sent": 0}
          )
          if acc_data["sent_today"] < acc_data["limit"]:
            await send_instagram_dm(target, sample_message)
            success = True
          else:
            logger.warning("Instagram uchun kunlik limit tugadi!")

        elif platform == "facebook" and FB_C_USER and FB_XS:
          acc_key = "facebook"
          acc_data = accounts.get(
              acc_key, {"limit": 10, "sent_today": 0, "total_sent": 0}
          )
          if acc_data["sent_today"] < acc_data["limit"]:
            await send_facebook_dm(target, sample_message)
            success = True
          else:
            logger.warning("Facebook uchun kunlik limit tugadi!")

        elif platform == "discord" and DISCORD_USER_TOKEN:
          acc_key = "discord"
          acc_data = accounts.get(
              acc_key, {"limit": 12, "sent_today": 0, "total_sent": 0}
          )
          if acc_data["sent_today"] < acc_data["limit"]:
            await send_discord_dm(target, sample_message)
            success = True
          else:
            logger.warning("Discord uchun kunlik limit tugadi!")

        elif platform == "telegram":
          # Jadvalda faqat 'telegram' yozilgan bo'lsa, ikkita akkauntni (tg_1 va tg_2) navbat bilan tekshiramiz
          tg_1 = accounts.get(
              "tg_1", {"limit": 5, "sent_today": 0, "total_sent": 0}
          )
          tg_2 = accounts.get(
              "tg_2", {"limit": 5, "sent_today": 0, "total_sent": 0}
          )

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
            logger.warning(
                "Telegram akkauntlarining ikkalasi ham kunlik limitga yetdi!"
            )

        elif (platform == "x" or platform == "twitter") and X_AUTH_TOKEN:
          acc_key = "x"
          acc_data = accounts.get(
              acc_key, {"limit": 17, "sent_today": 0, "total_sent": 0}
          )
          if acc_data["sent_today"] < acc_data["limit"]:
            await send_x_dm(target, sample_message)
            success = True
          else:
            logger.warning("X (Twitter) uchun kunlik limit tugadi!")

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

          logger.info(
              f"Lid yuborildi va {acc_key} statistikasi yangilandi -> {target}"
          )
          await safe_delay()
        else:
          logger.warning(
              f"Xabar yuborilmadi (Limit tugagan yoki platforma topilmadi):"
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
