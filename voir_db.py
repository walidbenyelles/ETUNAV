import sqlite3

# Connexion à la base
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Récupérer toutes les tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("=== STRUCTURE DE LA BASE DE DONNÉES ===\n")

# Pour chaque table, afficher son schéma
for table in tables:
    table_name = table[0]
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    schema = cursor.fetchone()
    
    if schema and schema[0]:
        print(f"TABLE: {table_name}")
        print("=" * 50)
        print(schema[0])
        print()

conn.close()

# Optionnel: liste simple des tables
print("\n=== LISTE DES TABLES ===")
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f"  - {table[0]}")

conn.close()
input("\nAppuie sur Entrée pour quitter...")