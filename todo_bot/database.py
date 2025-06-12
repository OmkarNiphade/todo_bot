import sqlite3

def init_db():
    conn = sqlite3.connect("todo.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            description TEXT,
            category TEXT,
            due_date TEXT,
            reminder_time TEXT,
            status TEXT DEFAULT 'active'
        )
    ''')
    conn.commit()
    conn.close()


def add_task_to_db(user_id, title, description, category, due_date, reminder_time):
    conn = sqlite3.connect("todo.db")
    c = conn.cursor()
    c.execute('''
        INSERT INTO tasks (user_id, title, description, category, due_date, reminder_time, status)
        VALUES (?, ?, ?, ?, ?, ?, 'active')
    ''', (user_id, title, description, category, due_date, reminder_time))
    conn.commit()
    conn.close()

def get_tasks_for_user(user_id):
    conn = sqlite3.connect("todo.db")
    c = conn.cursor()
    c.execute('''
        SELECT title, description, category, due_date, reminder_time
        FROM tasks
        WHERE user_id = ? AND status = 'active'
    ''', (user_id,))
    tasks = c.fetchall()
    conn.close()
    return tasks

def mark_task_inactive(user_id, title):
    conn = sqlite3.connect("todo.db")
    c = conn.cursor()
    c.execute("""
        UPDATE tasks
        SET status = 'inactive'
        WHERE user_id = ? AND title = ? AND status = 'active'
    """, (user_id, title))
    conn.commit()
    conn.close()

# 🔔 This function is used for scheduling reminders
def get_all_reminders():
    conn = sqlite3.connect("todo.db")
    c = conn.cursor()
    c.execute('''
        SELECT user_id, title, description, due_date, reminder_time
        FROM tasks
        WHERE status = 'active'
    ''')
    reminders = c.fetchall()
    conn.close()
    return reminders
