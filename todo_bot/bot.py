from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ConversationHandler,
    MessageHandler, ContextTypes, filters
)

from database import init_db, add_task_to_db, get_tasks_for_user, mark_task_inactive
from config import BOT_TOKEN
    
# ─────────── States ─────────── #
TITLE, DESCRIPTION, CATEGORY, DUE_DATE, REMINDER, REMOVE_SELECTION = range(6)

# ─────────── Handlers ─────────── #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to your Personal To-Do List Bot!\nUse /addtask, /viewtasks, /viewbycategory, /removetask."
    )

# ─────────── ADD TASK FLOW ─────────── #

async def add_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 What's the task title?")
    return TITLE

async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text
    await update.message.reply_text("✍️ Enter a short description:")
    return DESCRIPTION

async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text
    await update.message.reply_text("📂 Choose a category: Work, Personal, Misc")
    return CATEGORY

async def get_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = update.message.text.lower()
    if category not in ['work', 'personal', 'misc']:
        await update.message.reply_text("❗ Please choose: Work, Personal, or Misc")
        return CATEGORY
    context.user_data['category'] = category.capitalize()
    await update.message.reply_text("📅 Enter due date (YYYY-MM-DD):")
    return DUE_DATE

async def get_due_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['due_date'] = update.message.text
    await update.message.reply_text("⏰ Set reminder time (HH:MM in 24hr):")
    return REMINDER

async def get_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['reminder_time'] = update.message.text
    user_id = update.effective_user.id

    add_task_to_db(
        user_id=user_id,
        title=context.user_data['title'],
        description=context.user_data['description'],
        category=context.user_data['category'],
        due_date=context.user_data['due_date'],
        reminder_time=context.user_data['reminder_time'],
    )

    await update.message.reply_text("✅ Task added successfully!")
    return ConversationHandler.END

# ─────────── VIEW TASKS ─────────── #

async def view_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tasks = get_tasks_for_user(user_id)

    if not tasks:
        await update.message.reply_text("📭 You have no tasks.")
        return

    msg = "📝 *Your Tasks:*\n\n"
    for i, task in enumerate(tasks, 1):
        title, desc, cat, due, remind = task
        msg += f"*{i}. {title}* [{cat}]\n📌 {desc}\n📅 Due: {due} ⏰ Remind: {remind}\n\n"

    await update.message.reply_text(msg, parse_mode="Markdown")

# ─────────── VIEW BY CATEGORY ─────────── #

async def view_by_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tasks = get_tasks_for_user(user_id)

    if not tasks:
        await update.message.reply_text("📭 You have no tasks.")
        return

    categories = {'Work': [], 'Personal': [], 'Misc': []}
    for task in tasks:
        title, desc, cat, due, remind = task
        categories.get(cat, categories['Misc']).append((title, desc, due, remind))

    msg = "📂 *Your Tasks by Category:*\n\n"
    for cat, cat_tasks in categories.items():
        if cat_tasks:
            msg += f"📁 *{cat}*\n"
            for i, (title, desc, due, remind) in enumerate(cat_tasks, 1):
                msg += f"{i}. *{title}*\n📌 {desc}\n📅 Due: {due} ⏰ {remind}\n\n"

    await update.message.reply_text(msg, parse_mode="Markdown")

# ─────────── REMOVE TASK FLOW ─────────── #

async def remove_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tasks = get_tasks_for_user(user_id)

    if not tasks:
        await update.message.reply_text("📭 You have no tasks to remove.")
        return ConversationHandler.END

    context.user_data["tasks"] = tasks
    msg = "🗑 *Select a task to remove:*\n\n"
    for i, task in enumerate(tasks, 1):
        title, desc, _, _, _ = task
        msg += f"{i}. {title} — {desc}\n"
    msg += "\nSend the task number to remove."
    await update.message.reply_text(msg, parse_mode="Markdown")
    return REMOVE_SELECTION

async def confirm_removal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        task_index = int(update.message.text.strip()) - 1
        tasks = get_tasks_for_user(user_id)

        if task_index < 0 or task_index >= len(tasks):
            await update.message.reply_text("Invalid task number.")
            return REMOVE_SELECTION

        title = tasks[task_index][0]
        mark_task_inactive(user_id, title)
        await update.message.reply_text("🗑 Task removed successfully.")
        return ConversationHandler.END

    except (ValueError, IndexError):
        await update.message.reply_text("❗ Invalid number. Please try again.")
        return REMOVE_SELECTION

# ─────────── CANCEL FLOW ─────────── #

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Task creation cancelled.")
    return ConversationHandler.END

# ─────────── MAIN ─────────── #

def main():
    init_db()
    print("✅ Bot is running...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add Task Handler
    add_conv = ConversationHandler(
        entry_points=[CommandHandler("addtask", add_task_start)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_category)],
            DUE_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_due_date)],
            REMINDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_reminder)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Remove Task Handler
    remove_conv = ConversationHandler(
        entry_points=[CommandHandler("removetask", remove_task)],
        states={
            REMOVE_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_removal)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("viewtasks", view_tasks))
    app.add_handler(CommandHandler("viewbycategory", view_by_category))
    app.add_handler(add_conv)
    app.add_handler(remove_conv)

    app.run_polling()

if __name__ == "__main__":
    main()
