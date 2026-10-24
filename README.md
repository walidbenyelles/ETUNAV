# 🎓 EtuNav — Plateforme d'accompagnement pour étudiants

EtuNav est une application web Flask qui aide les étudiants (algériens et français) à gérer leurs démarches administratives lors de leur installation en France ou de leur préparation au départ.

---

## 📋 Fonctionnalités

- **Inscription sécurisée** avec vérification par email (code à 6 chiffres)
- **Validation admin** des comptes avec envoi d'un lien d'activation
- **Dashboard personnalisé** selon le profil de l'étudiant :
  - 🇫🇷 Étudiant français → démarches d'installation en France
  - 🇩🇿 Étudiant algérien en Algérie → préparation au départ
  - 🇩🇿 Étudiant algérien en France → démarches d'installation
- **Suivi des démarches** avec progression par catégorie
- **Centre d'alertes** pour les documents qui expirent (Visa, Passeport, etc.)
- **Chat communautaire** par région
- **Notifications** en temps réel
- **Interface admin** complète (validation, modération chat, gestion des démarches)
- **Scheduler automatique** pour les rappels d'expiration visa par email

---

## 🛠️ Stack technique

| Composant | Technologie |
|---|---|
| Backend | Python / Flask 3.0 |
| Base de données | SQLite via Flask-SQLAlchemy |
| Emails | Flask-Mail (Gmail SMTP) |
| Scheduler | APScheduler |
| Frontend | HTML / CSS / Vanilla JS |
| Auth | Sessions Flask + Werkzeug (hash bcrypt) |

---

## 🚀 Installation

### 1. Cloner le projet

```bash
git clone <url-du-repo>
cd MONessaye
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configurer les variables d'environnement

Créer un fichier `.env` à la racine du projet :

```env
# Configuration Email (Gmail)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=votre_email@gmail.com
MAIL_PASSWORD=votre_app_password_gmail
MAIL_DEFAULT_SENDER=votre_email@gmail.com

# Clé secrète Flask
SECRET_KEY=une-cle-secrete-tres-longue-et-aleatoire
```

> ⚠️ **Important** : Pour Gmail, vous devez créer un [App Password](https://myaccount.google.com/apppasswords) (pas votre mot de passe habituel).

### 5. Initialiser la base de données

```bash
python init_db.py
```

### 6. (Optionnel) Créer un compte administrateur

```bash
python create_admin.py
```

### 7. (Optionnel) Peupler les démarches par défaut

```bash
python seed_demarches.py
```

### 8. Lancer l'application

```bash
python app.py
```

L'application est accessible sur : **http://localhost:5000**

---

## 📁 Structure du projet

```
MONessaye/
├── app.py                  # Application principale (routes, logique)
├── models.py               # Modèles SQLAlchemy
├── config.py               # Configuration Flask
├── .env                    # Variables d'environnement (NON commité)
├── requirements.txt        # Dépendances Python
├── init_db.py              # Initialisation de la base de données
├── create_admin.py         # Création d'un compte admin
├── seed_demarches.py       # Données de démarches par défaut
├── migrate_db.py           # Migration de la base
├── reset_database.py       # Reset complet de la base
├── voir_db.py              # Inspection de la base
├── static/
│   ├── css/                # Feuilles de style
│   ├── js/                 # Scripts JavaScript
│   ├── images/             # Images
│   └── uploads/            # Fichiers uploadés par les utilisateurs
└── templates/
    ├── base.html           # Template de base
    ├── index.html          # Page d'accueil
    ├── login.html          # Connexion
    ├── register.html       # Inscription
    ├── verify_email.html   # Vérification email
    ├── dashboard_floating.html  # Dashboard principal
    ├── alerts.html         # Centre d'alertes
    ├── chat.html           # Chat communautaire
    ├── diagnostic.html     # Diagnostic profil
    ├── algerian_setup.html # Configuration étudiant algérien
    ├── admin/              # Templates admin
    └── emails/             # Templates d'emails
```

---

## 👤 Rôles utilisateurs

| Rôle | Description |
|---|---|
| **Visiteur** | Peut s'inscrire et se connecter |
| **Étudiant** | Accède à son dashboard, suivi des démarches, alertes, chat |
| **Admin** | Valide les comptes, modère le chat, gère les démarches |

---

## 🔐 Sécurité

- Mots de passe hashés avec Werkzeug (PBKDF2-SHA256)
- Sessions sécurisées avec cookie HttpOnly
- Vérification par email obligatoire à l'inscription
- Validation manuelle par admin avant activation du compte
- Fichiers uploadés accessibles uniquement aux admins

---

## 📧 Emails automatiques

| Événement | Email envoyé |
|---|---|
| Inscription | Code de vérification à 6 chiffres |
| Validation admin | Lien d'activation du compte |
| Visa expirant | Rappel tous les 4 jours (J-X) |
| Document expirant | Rappel si expiration dans les 30 jours |

---

## 📜 Licence

MIT — voir [LICENSE](LICENSE)