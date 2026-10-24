# Détail des Modifications Techniques (V2)

Ce document répertorie précisément les changements effectués pour rétablir le chat communautaire, corriger l'accès Admin et mettre en place le système d'alertes récurrentes.

## 1. Modèles de Données (`models.py`)

Le modèle `ChatMessage` manquait à l'appel. Il a été rajouté pour stocker les messages par région.

### Ajout du modèle ChatMessage
(Voir V1...)

### Correction du modèle Admin
L'accès était bloqué car les fonctions `check_password` et `set_password` n'étaient pas indentées dans la classe. Elles ont été déplacées à l'intérieur.
```python
# Ligne 67
class Admin(db.Model):
    # ...
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
```

### Support des Alerts Récurrentes
Remplacement de `last_alert_level` par `last_alert_date` pour suivre précisément le dernier envoi.
```python
# User et AlertDocument
last_visa_alert_date = db.Column(db.DateTime, default=None)
```

## 2. Logique Serveur (`app.py`)

Plusieurs modifications ont été apportées pour importer le modèle, créer les routes manquantes et sécuriser l'envoi des mails.

### Importations
```python
# Ligne 10 modifier pour inclure ChatMessage
from models import db, User, Admin, DemarcheStep, UserProgress, Notification, AlertDocument, DemarcheCategory, ChatMessage 
```

### Système de Rappel (7 jours)
Les alertes sont désormais envoyées **tous les 7 jours** si le document est toujours à moins de 30 jours de l'échéance.

```python
# app.py Ligne 397+
if days_left <= 30:
    if last_alert_date is None or (datetime.utcnow() - last_alert_date).days >= 7:
        send_email()
        last_alert_date = datetime.utcnow()
```

### Nouvelles Routes pour le Chat
Ces routes permettent au template `chat.html` de fonctionner correctement.

```python
# Ajoutées à la fin du fichier avant le démarrage du scheduler
@app.route('/chat')
def chat_page(): ... # Sert la page HTML

@app.route('/api/chat/<region>')
def api_get_chat(region): ... # Récupère les messages (JSON)

@app.route('/api/chat/send', methods=['POST'])
def api_send_chat(): ... # Enregistre un nouveau message
```

## 3. Nouveaux Fichiers

- **`templates/emails/alert_visa.html`** : Nouveau template pour l'email d'alerte avec un design moderne aux couleurs d'Etunav.
