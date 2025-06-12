from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from telegram import Bot

scheduler = BackgroundScheduler()
scheduler.start()

BOT_TOKEN = "your-bot-token"
bot = Bot(token=BOT_TOKEN)

def send_reminder(user_id, task_title):
    bot.send_message(chat_id=user_id, text=f"🔔 Reminder: {task_title}")

def schedule_reminder(user_id, task_title, reminder_time):
    dt = datetime.strptime(reminder_time, "%Y-%m-%d %H:%M")
    scheduler.add_job(send_reminder, 'date', run_date=dt, args=[user_id, task_title])
