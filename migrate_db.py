import sqlite3
import os

db_path = 'database.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Ajouter les nouvelles colonnes
        cursor.execute("ALTER TABLE users ADD COLUMN last_visa_alert_date DATETIME")
        print("✓ Colonne last_visa_alert_date ajoutée à users")
    except sqlite3.OperationalError:
        print("! Colonne last_visa_alert_date existe déjà dans users")

    try:
        cursor.execute("ALTER TABLE alert_documents ADD COLUMN last_alert_date DATETIME")
        print("✓ Colonne last_alert_date ajoutée à alert_documents")
    except sqlite3.OperationalError:
        print("! Colonne last_alert_date existe déjà dans alert_documents")
        
    conn.commit()
    conn.close()
    print("✓ Migration terminée")
else:
    print("! Base de données introuvable")
