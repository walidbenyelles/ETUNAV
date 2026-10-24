"""
Script pour réinitialiser la base de données avec les nouveaux champs de diagnostic
IMPORTANT: Fermez toute application utilisant database.db avant d'exécuter ce script
"""
import os
import sys
import time
from pathlib import Path

def reset_database():
    """Supprime et recrée la base de données"""
    # Chemin de la base de données
    db_path = Path('database.db')
    
    print("=== Réinitialisation de la base de données ===\n")
    
    # Supprimer l'ancienne base si elle existe
    if db_path.exists():
        try:
            db_path.unlink()
            print("✓ Ancienne base de données supprimée")
        except PermissionError:
            print("❌ ERREUR: La base de données est verrouillée!")
            print("   Solutions:")
            print("   1. Fermez toutes les connexions à la base (serveur Flask, etc.)")
            print("   2. Redémarrez votre terminal")
            print("   3. Supprimez manuellement database.db")
            sys.exit(1)
    
    # Créer les nouvelles tables avec les champs mis à jour
    from app import app
    from models import db
    
    with app.app_context():
        db.create_all()
        print("✓ Nouvelle base de données créée avec succès\n")
        print("Champs ajoutés au modèle User:")
        print("  - diagnostic_completed (Boolean)")
        print("  - situation (String)")
        print("  - date_entree_france (Date)")
        print("  - date_fin_visa (Date)")
        print("\n✅ Base de données prête à l'emploi")

if __name__ == '__main__':
    reset_database()
