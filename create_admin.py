"""
Script pour créer un compte administrateur
À utiliser après reset_database.py
"""
from app import app, db
from models import Admin

def create_admin():
    """Crée un compte admin dans la base existante"""
    with app.app_context():
        # Vérifier si un admin existe déjà
        admin_exists = Admin.query.filter_by(username='admin').first()
        
        if admin_exists:
            print("✓ Un compte admin existe déjà")
            print(f"   Username: {admin_exists.username}")
            return
        
        # Créer un nouveau compte admin
        admin = Admin(username='admin')
        admin.set_password('admin123')  # À CHANGER EN PRODUCTION !
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Compte admin créé avec succès!")
        print("\n📋 Identifiants:")
        print("   Username: admin")
        print("   Password: admin123")
        print("\n⚠️  IMPORTANT: Changez ce mot de passe en production!")
        print("\n🔗 Accès admin: http://localhost:5000/admin/login")

if __name__ == '__main__':
    try:
        create_admin()
    except Exception as e:
        print(f"❌ Erreur: {e}")
