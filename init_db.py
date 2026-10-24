"""
Script pour initialiser la base de données
Crée les tables et un compte admin par défaut
"""
import sys
from app import app, db
from models import User, Admin

def init_database():
    """Initialise la base de données et crée un compte admin"""
    with app.app_context():
        # Supprimer toutes les tables existantes
        db.drop_all()
        print("✓ Tables supprimées")
        
        # Créer toutes les tables
        db.create_all()
        print("✓ Tables créées")
        
        # Créer un compte admin par défaut
        admin_exists = Admin.query.filter_by(username='admin').first()
        if not admin_exists:
            admin = Admin(username='admin')
            admin.set_password('admin123')  # À CHANGER EN PRODUCTION !
            db.session.add(admin)
            db.session.commit()
            print("\n✅ Compte admin créé:")
            print("   Username: admin")
            print("   Password: admin123")
            print("\n⚠️  IMPORTANT: Changez ce mot de passe en production !")
        else:
            print("\n✓ Compte admin existe déjà")
        
        print("\n✅ Base de données initialisée avec succès!")

if __name__ == '__main__':
    try:
        init_database()
    except Exception as e:
        print(f"\n❌ Erreur lors de l'initialisation: {e}")
        sys.exit(1)
