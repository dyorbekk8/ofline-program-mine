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
import httpx

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
IG_SESSION_ID = os.getenv("IG_SESSION_ID")


# ==========================================
# 1. HAQIQIY YUBORISH FUNKSIYALARI
# ==========================================

async def send_telegram_dm(session_string, target, message):
  if not session_string or not API_ID or not API_HASH:
    raise Exception("Telegram sessiyasi yoki API ID/HASH yetishmayapti!")
  
  # Target'dan @ belgisini olib tashlaymiz (agar bo'lsa)
  target = target.strip()
  
  client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
  await client.connect()
  try:
    await client.send_message(target, message)
    logger.info(f"[Telegram Real] Xabar muvaffaqiyatli ketdi -> {target}")
  finally:
    await client.disconnect()


async def send_discord_dm(target, message):
  if not DISCORD_USER_TOKEN:
    raise Exception("Discord User Token topilmadi!")
  
  target_id = str(target).strip()
  headers = {
      "Authorization": DISCORD_USER_TOKEN,
      "Content-Type": "application/json"
  }
  
  async with httpx.AsyncClient() as client:
    # 1. DM kanalini ochish
    dm_payload = {"recipient_id": target_id}
    dm_res = await client.post(
        "https://discord.com/api/v9/users/@me/channels",
        headers=headers,
        json=dm_payload
    )
    
    if dm_res.status_code not in [200, 201]:
      raise Exception(f"Discord DM kanal ochilmadi! Code: {dm_res.status_code}, Xato: {dm_res.text}")
    
    channel_id = dm_res.json().get("id")
    
    # 2. Xabarni yuborish
    msg_payload = {"content": message}
    msg_res = await client.post(
        f"https://discord.com/api/v9/channels/{channel_id}/messages",
        headers=headers,
        json=msg_payload
    )
    
    if msg_res.status_code != 200:
      raise Exception(f"Discord xabar bormadi! Code: {msg_res.status_code}, Xato: {msg_res.text}")
      
    logger.info(f"[Discord Real] Xabar muvaffaqiyatli ketdi -> {target}")


async def send_instagram_dm(target, message):
  if not IG_SESSION_ID:
    raise Exception("Instagram Session ID topilmadi!")
  
  def _ig_sync_send():
    from instagrapi import Client
    cl = Client()
    cl.login_by_sessionid(IG_SESSION_ID)
    clean_target = target.replace('@', '').strip()
    user_id = cl.user_id_from_username(clean_target)
    cl.direct_send(message, user_ids=[user_id])
    
  # instagrapi sinxron ishlagani uchun uni asinxron thread'ga o'raymiz
  await asyncio.to_thread(_ig_sync_send)
  logger.info(f"[Instagram Real] Xabar muvaffaqiyatli ketdi -> {target}")


async def safe_delay():
  # Xavfsizlik uchun 15 - 30 daqiqa pauza
  delay_seconds = random.randint(900, 1800)
  delay_minutes = delay_seconds // 60
  logger.info(f"Xavfsizlik taymeri: {delay_minutes} daqiqa ({delay_seconds} soniya) kutilmoqda...")
  await asyncio.sleep(delay_seconds)


# ==========================================
# 2. ASOSIY BOT SIKLI
# ==========================================

async def outreach_loop():
  logger.info("Outreach bot TO'LIQ REAL rejimda ishga tushdi...")

  while True:
    try:
      config = get_config("LeadsBot")
      today = datetime.now().strftime("%Y-%m-%d")

      last_run_date = config.get("last_run_date", "")
      accounts = config.get("accounts", {})

      # Kun o'zgarganda limitlarni yangilash
      if last_run_date != today:
        update_last_run_date(today, "LeadsBot")
        reset_daily_counts("LeadsBot")
        config = get_config("LeadsBot")
        accounts = config.get("accounts", {})
        logger.info("Yangi kun boshlandi. Kunlik limitlar nollashtirildi.")

      pending_leads = get_pending_leads("LeadsBot")

      if not pending_leads:
        logger.info("Hozircha 'Pending' lidlar yo'q. 10 daqiqa kutamiz...")
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

        logger.info(f"Navbatdagi lid: {platform} -> {target}")

        try:
          if platform == "telegram":
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
              logger.warning("Telegram akkauntlarining limiti tugagan yoki Session yo'q!")

          elif platform == "discord":
            acc_key = "discord"
            acc_data = accounts.get(acc_key, {"limit": 12, "sent_today": 0, "total_sent": 0})
            if acc_data["sent_today"] < acc_data["limit"]:
              await send_discord_dm(target, sample_message)
              success = True
            else:
              logger.warning("Discord limiti tugagan!")

          elif platform == "instagram":
            acc_key = "instagram"
            acc_data = accounts.get(acc_key, {"limit": 10, "sent_today": 0, "total_sent": 0})
            if acc_data["sent_today"] < acc_data["limit"]:
              await send_instagram_dm(target, sample_message)
              success = True
            else:
              logger.warning("Instagram limiti tugagan!")

          elif platform in ["facebook", "x", "twitter"]:
            logger.warning(f"{platform.upper()} tarmog'iga xabar yuborish murakkab API talab qiladi. Hozircha o'tkazib yuborilmoqda.")
            # success = False bo'lib qolaveradi, jadvalga "Sent" deb yozilmaydi.
            await asyncio.sleep(5)
            continue
            
          else:
            logger.warning(f"Noma'lum platforma kiritildi: {platform}")

        except Exception as send_error:
          success = False
          logger.error(f"[{platform.upper()} XATOLIGI] {target} ga bormadi: {send_error}")

        # ======= FAQAT MUVAFFAQIYATLI YUBORILSA JADVAL YANGILANADI =======
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

          logger.info(f"Lid yopildi (Sent). {acc_key} statistikasi yangilandi. Kutish boshlanmoqda...")
          await safe_delay()
        else:
          logger.warning(f"Xabar yuborilmadi! {target} 'Pending' holatida qoldi. Keyingisiga o'tamiz...")
          await asyncio.sleep(10) # Xato bo'lsa 10 soniya kutib keyingisiga o'tadi

    except Exception as e:
      logger.error(f"Dastur ishlashida umumiy xato: {e}")
      await asyncio.sleep(60)


if __name__ == "__main__":
  try:
    asyncio.run(outreach_loop())
  except KeyboardInterrupt:
    logger.info("Bot to'xtatildi.")
