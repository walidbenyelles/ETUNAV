
from flask_sqlalchemy import SQLAlchemy 
from datetime import datetime 
from werkzeug.security import generate_password_hash, check_password_hash 
 
db = SQLAlchemy() 
 
class User(db.Model): 
    """Modèle pour les utilisateurs (étudiants)""" 
    __tablename__ = 'users' 
     
    id = db.Column(db.Integer, primary_key=True) 
    email = db.Column(db.String(120), unique=True, nullable=False, index=True) 
    password_hash = db.Column(db.String(255), nullable=False) 
    nom = db.Column(db.String(100), nullable=False) 
    prenom = db.Column(db.String(100), nullable=False) 
    nationalite = db.Column(db.String(100), nullable=False) 
    document_path = db.Column(db.String(255), nullable=False)  # Chemin du justificatif 
     
    # Statuts 
    is_verified = db.Column(db.Boolean, default=False)  # Validé par admin 
    is_active = db.Column(db.Boolean, default=False)    # Compte activé par email 
    is_banned = db.Column(db.Boolean, default=False)    # Compte banni par admin 
 # Diagnostic initial 
    diagnostic_completed = db.Column(db.Boolean, default=False)  # Diagnostic fait ? 
    situation = db.Column(db.String(20))  # 'algerie' ou 'france' pour étudiants algériens 
    date_entree_france = db.Column(db.Date)  # Pour étudiants algériens en France 
    date_fin_visa = db.Column(db.Date)  # Pour étudiants algériens en France 
    last_visa_alert_date = db.Column(db.DateTime, default=None)  # Date du dernier envoi
    # Token d'activation 
    activation_token = db.Column(db.String(100), unique=True) 
     
    # Timestamps 
    created_at = db.Column(db.DateTime, default=datetime.utcnow) 
    validated_at = db.Column(db.DateTime)  # Quand l'admin a validé 
    activated_at = db.Column(db.DateTime)  # Quand l'utilisateur a activé 
    last_login = db.Column(db.DateTime) 

    def set_password(self, password): 
        """Hash le mot de passe""" 
        self.password_hash = generate_password_hash(password) 
     
    def check_password(self, password): 
        """Vérifie le mot de passe""" 
        return check_password_hash(self.password_hash, password) 
     
    @property 
    def is_authenticated(self): 
        """Propriété pour vérifier si l'utilisateur est authentifié""" 
        return True 
     
    @property 
    def full_name(self): 
        """Retourne le nom complet""" 
        return f"{self.prenom} {self.nom}"
    def __repr__(self):
        return f'<User {self.email}>'
class Admin(db.Model): 
    """Modèle pour les administrateurs""" 
    __tablename__ = 'admins' 
     
    id = db.Column(db.Integer, primary_key=True) 
    username = db.Column(db.String(80), unique=True, nullable=False) 
    password_hash = db.Column(db.String(255), nullable=False) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        """Hash le mot de passe"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Vérifie le mot de passe"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Admin {self.username}>'

class ChatMessage(db.Model):
    """Modèle pour les messages du chat communautaire"""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user_name = db.Column(db.String(100), nullable=False)  # Cache pour éviter les jointures
    content = db.Column(db.Text, nullable=False)
    region = db.Column(db.String(50), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('chat_messages', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'content': self.content,
            'region': self.region,
            'timestamp': self.timestamp.strftime('%H:%M')
        }

class DemarcheCategory(db.Model): 
    """Catégories de démarches (Visa, Logement, Aides, etc.)""" 
    __tablename__ = 'demarche_categories' 
     
    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(100), nullable=False) 
    emoji = db.Column(db.String(10), nullable=False)  # Emoji représentatif 
    description = db.Column(db.Text) 
    color = db.Column(db.String(7), default='#667eea')  # Couleur hex 
    order_index = db.Column(db.Integer, default=0)  # Ordre d'affichage 
    target_profile = db.Column(db.String(50))  # 'algerie', 'france', 'fr' ou 'all'
    
    # Relation
    steps = db.relationship('DemarcheStep', backref='category', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Category {self.name}>'


    
#walid amine

class DemarcheStep(db.Model): 
    """Étapes individuelles de démarches""" 
    __tablename__ = 'demarche_steps' 
     
    id = db.Column(db.Integer, primary_key=True) 
    category_id = db.Column(db.Integer, db.ForeignKey('demarche_categories.id'), nullable=False) 
    title = db.Column(db.String(200), nullable=False) 
    description = db.Column(db.Text) 
    priority = db.Column(db.Integer, default=2)  # 1=Essentiel, 2=Important, 3=Recommandé 
    # Données JSON
    documents_needed = db.Column(db.Text)  # JSON array de documents
    sub_steps = db.Column(db.Text)  # JSON array de sous-étapes
    resources = db.Column(db.Text)  # JSON array d'objets {label, url}
    
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    progress_records = db.relationship('UserProgress', backref='step', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Step {self.title}>'


class UserProgress(db.Model):
    """Suivi de progression pour chaque utilisateur"""
    __tablename__ = 'user_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    step_id = db.Column(db.Integer, db.ForeignKey('demarche_steps.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)  # Notes personnelles de l'utilisateur
#walid amine
    # Index composé pour éviter doublons
    __table_args__ = (db.UniqueConstraint('user_id', 'step_id', name='_user_step_uc'),)
    
    def __repr__(self):
        return f'<Progress User:{self.user_id} Step:{self.step_id} Done:{self.completed}>'


class Notification(db.Model):
    """Système de notifications"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Optional metadata
    link = db.Column(db.String(255))
    icon = db.Column(db.String(50), default='ri-notification-3-line')
    
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic', cascade='all, delete-orphan'))
    
class AlertDocument(db.Model):
    """Documents personnalisés à surveiller"""
    __tablename__ = 'alert_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)       # ex: "Passeport"
    expiry_date = db.Column(db.Date, nullable=False)        # Date d'expiration
    last_alert_date = db.Column(db.DateTime, default=None)  # Date du dernier envoi (anti-doublon)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('alert_documents', lazy='dynamic', cascade='all, delete-orphan'))

