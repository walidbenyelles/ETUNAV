import sqlite3
import json

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

def get_count(table):
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        return cursor.fetchone()[0]
    except Exception as e:
        return f"Error: {e}"

stats = {
    'users_count': get_count('users'),
    'admins_count': get_count('admins'),
    'demarche_categories_count': get_count('demarche_categories'),
    'demarche_steps_count': get_count('demarche_steps'),
    'chat_messages_count': get_count('chat_messages'),
    'notifications_count': get_count('notifications'),
    'alert_documents_count': get_count('alert_documents'),
    'user_progress_count': get_count('user_progress')
}

cursor.execute("SELECT id, email, nom, prenom, nationalite, situation, is_verified, is_active, is_banned, diagnostic_completed, date_entree_france, date_fin_visa, password_hash FROM users")
users = []
for row in cursor.fetchall():
    users.append({
        'id': row[0],
        'email': row[1],
        'nom': row[2],
        'prenom': row[3],
        'nationalite': row[4],
        'situation': row[5],
        'is_verified': bool(row[6]),
        'is_active': bool(row[7]),
        'is_banned': bool(row[8]),
        'diagnostic_completed': bool(row[9]),
        'date_entree_france': str(row[10]),
        'date_fin_visa': str(row[11]),
        'password_hash_prefix': row[12][:25] + '...' if row[12] else None
    })

cursor.execute("SELECT id, username FROM admins")
admins = [{'id': r[0], 'username': r[1]} for r in cursor.fetchall()]

cursor.execute("SELECT id, name, emoji, target_profile FROM demarche_categories")
categories = [{'id': r[0], 'name': r[1], 'emoji': r[2], 'target_profile': r[3]} for r in cursor.fetchall()]

cursor.execute("SELECT id, category_id, title, priority FROM demarche_steps")
steps = [{'id': r[0], 'category_id': r[1], 'title': r[2], 'priority': r[3]} for r in cursor.fetchall()]

print(json.dumps({
    'stats': stats,
    'admins': admins,
    'users': users,
    'categories': categories,
    'steps_count_by_category': len(steps)
}, indent=2, ensure_ascii=False))

conn.close()
