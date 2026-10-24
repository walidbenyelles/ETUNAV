import os 
import secrets 
import random 
import json 
from datetime import datetime, timedelta 
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, jsonify 
from flask_mail import Mail, Message 
from werkzeug.utils import secure_filename 
from config import Config 
from models import db, User, Admin, DemarcheStep, UserProgress, Notification, AlertDocument, DemarcheCategory, ChatMessage 
 
app = Flask(__name__) 
app.config.from_object(Config) 
# Initialisation des extensions 
db.init_app(app) 
mail = Mail(app) 
 
# Créer le dossier uploads s'il n'existe pas 

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) 


def allowed_file(filename):
    """Vérifie si l'extension du fichier est autorisée"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def send_verification_code_email(email, code):
    """Envoie l'email avec le code de vérification"""
    try:
        msg = Message(
            'Code de vérification - Etudiant Portal',
            recipients=[email]
        )
        msg.html = render_template('emails/verification_code.html', code=code)
        mail.send(msg)
        print(f"--- DEBUG: Code de vérification pour {email} : {code} ---")
        return True
    except Exception as e:
        print(f"Erreur lors de la simulation de l'envoi du code: {e}")
        return False

def send_activation_email(user):
    """Envoie l'email d'activation à l'utilisateur"""
    try:
        msg = Message(
            'Votre compte a été validé !',
            recipients=[user.email]
        )
        
        activation_link = url_for('activate_account', token=user.activation_token, _external=True)
        
        msg.html = render_template('emails/activation.html',
                                   user=user,
                                   activation_link=activation_link)
        
        mail.send(msg)
        print(f"--- DEBUG: Lien d'activation pour {user.email} : {activation_link} ---")
        return True
    except Exception as e:
        print(f"Erreur lors de la simulation de l'envoi de l'email: {e}")
        return False

    # ==================== ROUTES PUBLIQUES ====================

@app.route('/')
def home():
    """Page d'accueil"""
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return render_template('index.html', user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Inscription - Étape 1: Formulaire et envoi du code"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        nom = request.form.get('nom')
        prenom = request.form.get('prenom')
        nationalite = request.form.get('nationalite')

        # Vérification du fichier
        if 'document' not in request.files:
            flash('Aucun fichier fourni', 'error')
            return redirect(request.url)

        file = request.files['document']

        if file.filename == '':
            flash('Aucun fichier sélectionné', 'error')
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash('Type de fichier non autorisé. Utilisez PDF, PNG, JPG ou JPEG', 'error')
            return redirect(request.url)

            # Vérifier si l'email existe déjà
        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà enregistré', 'error')
            return redirect(request.url)

            # Sauvegarder le fichier temporairement
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Générer un code de vérification à 6 chiffres
        verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])

        # Stocker dans la session
        session['verification_pending'] = {
            'email': email,
            'password': password,
            'nom': nom,
            'prenom': prenom,
            'nationalite': nationalite,
            'document_filename': filename,
            'code': verification_code,
            'expires_at': (datetime.now() + timedelta(minutes=10)).isoformat(),
            'attempts': 0
        }

        # Envoyer l'email avec le code
        if send_verification_code_email(email, verification_code):
            flash('Un code de vérification a été envoyé à votre email !', 'success')
            return redirect(url_for('verify_email'))
        else:
            flash('Erreur lors de l\'envoi de l\'email. Veuillez réessayer.', 'error')
            return redirect(request.url)

    return render_template('register.html')

@app.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    """Inscription - Étape 2: Vérification du code"""
    if 'verification_pending' not in session:
        flash('Session expirée. Veuillez vous réinscrire.', 'warning')
        return redirect(url_for('register'))

    pending = session['verification_pending']

    # Vérifier l'expiration
    expires_at = datetime.fromisoformat(pending['expires_at'])
    if datetime.now() > expires_at:
        flash('Le code a expiré. Veuillez vous réinscrire.', 'error')
        session.pop('verification_pending', None)
        return redirect(url_for('register'))

    if request.method == 'POST':
        entered_code = request.form.get('code', '').strip()

        # Incrémenter les tentatives
        pending['attempts'] += 1
        session['verification_pending'] = pending

        # Limiter à 5 tentatives
        if pending['attempts'] > 5:
            flash('Trop de tentatives. Veuillez vous réinscrire.', 'error')
            session.pop('verification_pending', None)
            return redirect(url_for('register'))

            # Vérifier le code
        if entered_code == pending['code']:
            # Code correct ! Créer l'utilisateur
            user = User(
                email=pending['email'],
                nom=pending['nom'],
                prenom=pending['prenom'],
                nationalite=pending['nationalite'],
                document_path=pending['document_filename'],
                activation_token=secrets.token_urlsafe(32)
            )
            user.set_password(pending['password'])

            db.session.add(user)
            db.session.commit()

            # Nettoyer la session
            session.pop('verification_pending', None)

            flash('   Email vérifié ! Votre demande est en attente de validation par un administrateur.', 'success')
            return redirect(url_for('login'))
        else:
            attempts_left = 5 - pending['attempts']
            flash(f'  Code incorrect. Il vous reste {attempts_left} tentative(s).', 'error')
            return redirect(request.url)

    return render_template('verify_email.html', email=pending['email'])

@app.route('/resend-verification-code')
def resend_verification_code():
    """Renvoyer le code de vérification"""
    if 'verification_pending' not in session:
        flash('Session expirée. Veuillez vous réinscrire.', 'warning')
        return redirect(url_for('register'))

    pending = session['verification_pending']

    # Générer un nouveau code
    new_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])

    # Mettre à jour la session
    pending['code'] = new_code
    pending['expires_at'] = (datetime.now() + timedelta(minutes=10)).isoformat()
    pending['attempts'] = 0
    session['verification_pending'] = pending

    # Renvoyer l'email
    if send_verification_code_email(pending['email'], new_code):
        flash('Un nouveau code a été envoyé à votre email !', 'success')
    else:
        flash('Erreur lors de l\'envoi. Veuillez réessayer.', 'error')

    return redirect(url_for('verify_email'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Connexion utilisateur"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            # Vérifier si le compte est validé par l'admin
            if not user.is_verified:
                flash('Votre compte n\'a pas encore été validé par un administrateur. Veuillez patienter.', 'warning')
                return redirect(request.url)

                # Vérifier si le compte est activé
            if not user.is_active:
                flash('Veuillez activer votre compte via le lien envoyé par email.', 'warning')
                return redirect(request.url)

                # Vérifier si le compte est banni
            if user.is_banned:
                flash('Votre compte a été suspendu par l\'administration.', 'error')
                return redirect(request.url)

                # Créer la session
            session['user_id'] = user.id
            session['user_email'] = user.email
            session.permanent = True

            # Mettre à jour la dernière connexion
            user.last_login = datetime.utcnow()
            db.session.commit()

            flash(f'Bienvenue {user.prenom} !              ', 'success')

            # Vérifier si le diagnostic a été complété
            if not user.diagnostic_completed:
                # Première connexion - rediriger vers le diagnostic approprié
                if user.nationalite == 'fr':
                    # Étudiants français vont directement au dashboard
                    user.diagnostic_completed = True
                    db.session.commit()
                    return redirect(url_for('dashboard'))
                else:
                    # Tous les autres (dont algériens) vont vers la nouvelle page d'installation
                    return redirect(url_for('diagnostic_algerie_setup'))

            return redirect(url_for('dashboard'))
        else:
            flash('Email ou mot de passe incorrect', 'error')

    return render_template('login.html')

@app.route('/activate/<token>')
def activate_account(token):
    """Activation du compte via le token"""
    user = User.query.filter_by(activation_token=token).first()

    if not user:
        flash('Token d\'activation invalide', 'error')
        return redirect(url_for('login'))

    if user.is_active:
        flash('Ce compte est déjà activé', 'info')
        return redirect(url_for('login'))

    user.is_active = True
    user.activated_at = datetime.utcnow()
    db.session.commit()

    flash('Compte activé avec succès ! Vous pouvez maintenant vous connecter.              ', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """Dashboard utilisateur"""
    if 'user_id' not in session:
        flash('Veuillez vous connecter pour accéder à cette page', 'warning')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        flash('Utilisateur introuvable', 'error')
        return redirect(url_for('login'))

        # Rediriger vers le dashboard approprié selon le profil
    if user.nationalite == 'fr':
        return redirect(url_for('dashboard_installation_france'))
    elif user.situation == 'algerie':
        return redirect(url_for('dashboard_preparation_depart'))
    elif user.situation == 'france':
        return redirect(url_for('dashboard_installation_algerie'))
    else:
        # Fallback pour les cas non traités
        return render_template('dashboard.html', user=user)


@app.route('/alerts')
def alerts_page():
    """Centre d'alertes utilisateur"""
    if 'user_id' not in session:
        flash('Veuillez vous connecter pour accéder à cette page', 'warning')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        flash('Utilisateur introuvable', 'error')
        return redirect(url_for('login'))
        
    # Vérifier l'alerte Visa
    visa_alert_active = False
    jours_restants_visa = -1
    
    if user.date_fin_visa:
        jours_restants_visa = (user.date_fin_visa - datetime.now().date()).days
        visa_alert_active = True
        titre_sejour_step = DemarcheStep.query.filter(DemarcheStep.title.ilike('%titre de séjour%')).first()
        if titre_sejour_step:
            progress = UserProgress.query.filter_by(user_id=user.id, step_id=titre_sejour_step.id, completed=True).first()
            if progress:
                visa_alert_active = False

    return render_template('alerts.html', user=user, visa_alert_active=visa_alert_active, jours_restants_visa=jours_restants_visa)

@app.route('/alerts/add', methods=['POST'])
def add_alert():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    name = request.form.get('doc_name')
    date_str = request.form.get('expiry_date')
    try:
        expiry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        doc = AlertDocument(user_id=session['user_id'], name=name, expiry_date=expiry_date)
        db.session.add(doc)
        db.session.commit()
        
        # Déclencher la vérification immédiate des alertes
        process_alerts()
        
        flash('Alerte ajoutée avec succès !', 'success')
    except Exception as e:
        flash("Erreur lors de l'ajout", 'error')
    return redirect(url_for('alerts_page'))

@app.route('/alerts/delete/<int:doc_id>', methods=['POST'])
def delete_alert(doc_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    doc = AlertDocument.query.get_or_404(doc_id)
    if doc.user_id == session['user_id']:
        db.session.delete(doc)
        db.session.commit()
        flash('Alerte supprimée.', 'success')
    return redirect(url_for('alerts_page'))

def process_alerts():
    """Fonction principale pour vérifier et envoyer les alertes"""
    """Route asynchrone pour vérifier et envoyer les alertes (à appeler via cron)"""
    users = User.query.all()
    titre_sejour_step = DemarcheStep.query.filter(DemarcheStep.title.ilike('%titre de séjour%')).first()
    
    for user_iter in users:
        # Check visa
        if user_iter.date_fin_visa:
            days_left = (user_iter.date_fin_visa - datetime.now().date()).days
            
            visa_alert_active = True
            if titre_sejour_step:
                progress = UserProgress.query.filter_by(user_id=user_iter.id, step_id=titre_sejour_step.id, completed=True).first()
                if progress:
                    visa_alert_active = False
            
            if visa_alert_active:
                    if days_left < 0:
                        continue  # Ne pas alerter si déjà expiré
                        
                    send_needed = False
                    if user_iter.last_visa_alert_date is None:
                        send_needed = True
                    else:
                        # Vérifier si 4 jours se sont écoulés depuis le dernier envoi
                        elapsed = (datetime.utcnow() - user_iter.last_visa_alert_date).days
                        if elapsed >= 4:
                            send_needed = True
                    
                    if send_needed:
                        try:
                            msg = Message(f"Alerte : Votre visa expire dans {days_left} jours", recipients=[user_iter.email])
                            msg.html = render_template('emails/alert_visa.html', user=user_iter, days_left=days_left, expiry_date=user_iter.date_fin_visa)
                            msg.body = f"Bonjour {user_iter.prenom}, votre visa expire le {user_iter.date_fin_visa}. Pensez à renouveler votre titre de séjour."
                            mail.send(msg)
                            
                            notif = Notification(
                                user_id=user_iter.id, 
                                title="⚠️ Rappel : Expiration Visa", 
                                message=f"Votre visa expire dans {days_left} jours. Pensez à entamer vos démarches.", 
                                icon='ri-alert-line',
                                link='/alerts'  # Lien statique car url_for hors contexte requête échoue
                            )
                            db.session.add(notif)
                            
                            # Mettre à jour la date de l'envoi
                            user_iter.last_visa_alert_date = datetime.utcnow()
                            db.session.commit() # Commit immédiat pour éviter doublon si crash suivant
                            print(f"✓ Notification (simulée) envoyée à {user_iter.email} (J-{days_left})")
                        except Exception as e:
                            db.session.rollback()
                            print(f"❌ Erreur critique d'envoi à {user_iter.email}: {e}")
                    
        # Check custom docs
        for doc in user_iter.alert_documents:
            days_left = (doc.expiry_date - datetime.now().date()).days
            if 30 >= days_left >= 0: # Ne pas alerter si expiré
                send_needed_doc = False
                if doc.last_alert_date is None:
                    send_needed_doc = True
                else:
                    elapsed_doc = (datetime.utcnow() - doc.last_alert_date).days
                    if elapsed_doc >= 4:
                        send_needed_doc = True
                
                if send_needed_doc:
                    try:
                        msg = Message(f"Alerte : Document {doc.name} expire bientôt", recipients=[user_iter.email])
                        msg.body = f"Bonjour,\nVotre document {doc.name} expire le {doc.expiry_date}. Pensez à le renouveler."
                        mail.send(msg)
                        
                        notif = Notification(
                            user_id=user_iter.id, 
                            title="⚠️ Rappel : Expiration Document", 
                            message=f"Le document {doc.name} expire dans {days_left} jours.", 
                            icon='ri-file-warning-line',
                            link='/alerts'
                        )
                        db.session.add(notif)
                        
                        doc.last_alert_date = datetime.utcnow()
                        db.session.commit()
                        print(f"✓ Notification document {doc.name} envoyée à {user_iter.email}")
                    except Exception as e:
                        db.session.rollback()
                        print(f"❌ Erreur d'envoi pour {doc.name} à {user_iter.email}: {e}")

@app.route('/api/cron/check-alerts')
def cron_check_alerts():
    """Route pour déclencher manuellement la vérification via URL (protégée par token)"""
    token = request.args.get('token', '')
    expected = app.config.get('SECRET_KEY', '')
    if not token or token != expected:
        return jsonify({'error': 'Unauthorized'}), 401
    process_alerts()
    return jsonify({'success': True, 'message': 'Alerts checked'})

# ==================== SCHEDULER (TÂCHES DE FOND) ====================
def start_scheduler():
    from apscheduler.schedulers.background import BackgroundScheduler
    import os
    
    # Éviter de lancer le scheduler deux fois avec l'auto-reloader de Flask
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        scheduler = BackgroundScheduler()
        
        def job_function():
            with app.app_context():
                process_alerts()
                
        # Le job s'exécute automatiquement en arrière-plan
        # On vérifie toutes les 24 heures (intervalle journalier)
        scheduler.add_job(func=job_function, trigger="interval", days=1)
        scheduler.start()

# ==================== ROUTES CHAT COMMUNAUTAIRE ====================

@app.route('/chat')
def chat_page():
    """Page du forum communautaire"""
    if 'user_id' not in session:
        flash('Veuillez vous connecter pour accéder au chat', 'warning')
        return redirect(url_for('login'))
        
    user = User.query.get(session['user_id'])
    return render_template('chat.html', user=user)

@app.route('/api/chat/<region>')
def api_get_chat(region):
    """Récupérer les messages d'une région"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    messages = ChatMessage.query.filter_by(region=region)\
        .order_by(ChatMessage.timestamp.asc())\
        .limit(50).all()
        
    return jsonify({
        'messages': [m.to_dict() for m in messages]
    })

@app.route('/api/chat/send', methods=['POST'])
def api_send_chat():
    """Envoyer un nouveau message"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.json
    region = data.get('region')
    content = data.get('content')
    
    if not region or not content:
        return jsonify({'error': 'Missing data'}), 400
        
    user = User.query.get(session['user_id'])
    
    msg = ChatMessage(
        user_id=user.id,
        user_name=f"{user.prenom} {user.nom[0]}.", # Format "Prénom N."
        content=content,
        region=region
    )
    
    db.session.add(msg)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': msg.to_dict()
    })

start_scheduler()

@app.route('/logout')
def logout():
    """Déconnexion utilisateur"""
    session.clear()
    flash('Vous avez été déconnecté avec succès', 'info')
    return redirect(url_for('home'))

# ==================== ROUTES DIAGNOSTIC ====================

@app.route('/diagnostic', methods=['GET', 'POST'])
def diagnostic():
    """Page de diagnostic pour étudiants algériens"""
    if 'user_id' not in session:
        flash('Veuillez vous connecter pour accéder à cette page', 'warning')
        return redirect(url_for('login'))
        
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        situation = request.form.get('situation')
        if situation == 'algerie':
            user.situation = 'algerie'
            user.diagnostic_completed = True
            db.session.commit()
            flash('Diagnostic complété ! Voici votre parcours de préparation.', 'success')
            return redirect(url_for('dashboard_preparation_depart'))
        elif situation == 'france':
            # Rediriger vers le formulaire de dates
            session['diagnostic_situation'] = 'france'
            return redirect(url_for('diagnostic_france_info'))
            
    return render_template('diagnostic.html', user=user)

@app.route('/diagnostic/algerie-setup', methods=['GET', 'POST'])
def diagnostic_algerie_setup():
    """Formulaire de dates pour étudiants algériens (et autres intl)"""
    if 'user_id' not in session:
        flash('Veuillez vous connecter', 'warning')
        return redirect(url_for('login'))
        
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))
        
    # Si déjà complété, on redirige vers le dashboard
    if user.diagnostic_completed:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        situation = request.form.get('situation')
        if situation == 'algerie':
            user.situation = 'algerie'
            user.diagnostic_completed = True
            db.session.commit()
            flash('Bienvenue ! Votre espace est prêt.', 'success')
            return redirect(url_for('dashboard'))
        elif situation == 'france':
            from datetime import datetime as dt
            date_entree_str = request.form.get('date_entree')
            date_fin_visa_str = request.form.get('date_fin_visa')
            
            if not date_entree_str or not date_fin_visa_str:
                flash('Veuillez fournir les deux dates pour la situation en France.', 'error')
                return redirect(request.url)
            try:
                date_entree = dt.strptime(date_entree_str, '%Y-%m-%d').date()
                date_fin_visa = dt.strptime(date_fin_visa_str, '%Y-%m-%d').date()
                if date_fin_visa <= date_entree:
                    flash('La date de sortie doit être postérieure à la date d\'entrée.', 'error')
                    return redirect(request.url)
                
                user.situation = 'france'
                user.date_entree_france = date_entree
                user.date_fin_visa = date_fin_visa
                user.diagnostic_completed = True
                db.session.commit()
                
                # Déclencher la vérification immédiate des alertes
                process_alerts()
                
                flash('Configuration terminée ! Vos alertes sont prêtes.', 'success')
                return redirect(url_for('dashboard'))
            except ValueError:
                flash('Format de date invalide.', 'error')
                return redirect(request.url)
        else:
            flash('Veuillez sélectionner une situation.', 'error')
            return redirect(request.url)
            
    return render_template('algerian_setup.html', user=user)

@app.route('/diagnostic/france-info', methods=['GET', 'POST'])
def diagnostic_france_info():
    """Formulaire de dates (Legacy)"""
    if 'user_id' not in session:
        flash('Veuillez vous connecter', 'warning')
        return redirect(url_for('login'))
        
    if 'diagnostic_situation' not in session or session['diagnostic_situation'] != 'france':
        return redirect(url_for('diagnostic'))
        
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        from datetime import datetime as dt
        date_entree_str = request.form.get('date_entree')
        date_fin_visa_str = request.form.get('date_fin_visa')
        try:
            date_entree = dt.strptime(date_entree_str, '%Y-%m-%d').date()
            date_fin_visa = dt.strptime(date_fin_visa_str, '%Y-%m-%d').date()
            if date_fin_visa <= date_entree:
                flash('La date de fin de visa doit être postérieure à la date d\'entrée', 'error')
                return redirect(request.url)
                
            user.situation = 'france'
            user.date_entree_france = date_entree
            user.date_fin_visa = date_fin_visa
            user.diagnostic_completed = True
            db.session.commit()
            
            # Déclencher la vérification immédiate des alertes
            process_alerts()
            
            session.pop('diagnostic_situation', None)
            flash('Diagnostic complété ! Vos alertes sont configurées.', 'success')
            return redirect(url_for('dashboard_installation_algerie'))
        except ValueError:
            flash('Format de date invalide', 'error')
            return redirect(request.url)
            
    return render_template('diagnostic_france_info.html', user=user)

# ==================== ROUTES DASHBOARD ====================

@app.route('/dashboard/installation-france')
def dashboard_installation_france():
    """Dashboard pour étudiants français"""
    if 'user_id' not in session:
        flash('Veuillez vous connecter', 'warning')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))
    return render_template('dashboard_floating.html', user=user)

@app.route('/dashboard/preparation-depart')
def dashboard_preparation_depart():
    """Dashboard pour étudiants algériens en Algérie"""
    if 'user_id' not in session:
        flash('Veuillez vous connecter', 'warning')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))
    return render_template('dashboard_floating.html', user=user)

@app.route('/dashboard/installation-algerie')
def dashboard_installation_algerie():
    """Dashboard pour étudiants algériens en France"""
    if 'user_id' not in session:
        flash('Veuillez vous connecter', 'warning')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))
    
    jours_restants = None
    if user.date_fin_visa:
        from datetime import datetime as dt
        delta = user.date_fin_visa - dt.now().date()
        jours_restants = delta.days
    return render_template('dashboard_floating.html', user=user, jours_restants=jours_restants)

# ==================== ROUTES ADMIN (SPRINT 1 ) ====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Connexion administrateur"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            flash('Connexion admin réussie', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Identifiants incorrects', 'error')
    return render_template('admin/login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    """Dashboard administrateur"""
    if 'admin_id' not in session:
        flash('Accès refusé', 'error')
        return redirect(url_for('admin_login'))
    stats = {
        'total': User.query.count(),
        'pending': User.query.filter_by(is_verified=False).count(),
        'verified': User.query.filter_by(is_verified=True).count(),
        'active': User.query.filter_by(is_active=True).count()
    }
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/pending')
def admin_pending():
    """Liste des demandes d'inscription en attente"""
    if 'admin_id' not in session:
        flash('Accès refusé', 'error')
        return redirect(url_for('admin_login'))
    pending_users = User.query.filter_by(is_verified=False).order_by(User.created_at.desc()).all()
    return render_template('admin/pending.html', users=pending_users)

@app.route('/admin/validate/<int:user_id>')
def admin_validate(user_id):
    """Valider une demande d'inscription"""
    if 'admin_id' not in session:
        flash('Accès refusé', 'error')
        return redirect(url_for('admin_login'))
    user = User.query.get_or_404(user_id)
    if user.is_verified:
        flash('Cet utilisateur est déjà validé', 'info')
        return redirect(url_for('admin_pending'))
        
    user.is_verified = True
    user.validated_at = datetime.utcnow()
    db.session.commit()
    
    send_activation_email(user)
    
    notif = Notification(
        user_id=user.id,
        title="✓ Compte validé !",
        message="Votre compte a été validé par un administrateur. Vous pouvez maintenant configurer votre intégration.",
        icon="ri-check-double-line"
    )
    db.session.add(notif)
    db.session.commit()
    flash(f'✓ Utilisateur {user.email} validé !', 'success')
    return redirect(url_for('admin_pending'))

@app.route('/admin/reject/<int:user_id>')
def admin_reject(user_id):
    """Rejeter une demande d'inscription"""
    if 'admin_id' not in session:
        flash('Accès refusé', 'error')
        return redirect(url_for('admin_login'))
    user = User.query.get_or_404(user_id)
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], user.document_path)
    if os.path.exists(file_path):
        os.remove(file_path)
        
    db.session.delete(user)
    db.session.commit()
    flash(f'Demande de {user.email} rejetée et supprimée', 'success')
    return redirect(url_for('admin_pending'))
@app.route('/admin/chat')
def admin_chat():
    """Modération du Chat"""
    if 'admin_id' not in session:
        flash('Accès refusé', 'error')
        return redirect(url_for('admin_login'))
        
    region = request.args.get('region', '')
    query = ChatMessage.query
    if region:
        query = query.filter_by(region=region)
        
    messages = query.order_by(ChatMessage.timestamp.desc()).all()
    # Récupérer les régions uniques
    regions = db.session.query(ChatMessage.region).distinct().all()
    regions = [r[0] for r in regions]
    
    return render_template('admin/chat.html', messages=messages, regions=regions, selected_region=region)


@app.route('/admin/chat/delete/<int:msg_id>', methods=['POST'])
def admin_delete_chat(msg_id):
    """Supprimer un message"""
    if 'admin_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    msg = ChatMessage.query.get_or_404(msg_id)
    db.session.delete(msg)
    db.session.commit()
    
    return jsonify({'success': True})



@app.route('/admin/user/ban/<int:user_id>', methods=['POST'])
def admin_ban_user(user_id):
    """Bannir/Débannir un utilisateur"""
    if 'admin_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.get_or_404(user_id)
    user.is_banned = not user.is_banned
    db.session.commit()

    return jsonify({'success': True, 'is_banned': user.is_banned})


@app.route('/admin/demarches', methods=['GET', 'POST'])
def admin_demarches():
    """Gestion des démarches (Création de catégorie)"""
    if 'admin_id' not in session:
        flash('Accès refusé', 'error')
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        name = request.form.get('name')
        emoji = request.form.get('emoji', '📄')
        desc = request.form.get('description', '')
        target = request.form.get('target', 'all')
        color = request.form.get('color', '#667eea')

        cat = DemarcheCategory(
            name=name,
            emoji=emoji,
            description=desc,
            target_profile=target,
            color=color
        )
        db.session.add(cat)
        db.session.commit()
        flash('Catégorie ajoutée avec succès !', 'success')
        return redirect(url_for('admin_demarches'))

    categories = DemarcheCategory.query.order_by(DemarcheCategory.order_index).all()
    return render_template('admin/demarches.html', categories=categories)


@app.route('/admin/demarches/<int:cat_id>/step', methods=['POST'])
def admin_add_step(cat_id):
    """Ajouter une étape à une catégorie"""
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    cat = DemarcheCategory.query.get_or_404(cat_id)
    title = request.form.get('title')
    desc = request.form.get('description', '')

    # Validation du json (documents)
    docs_raw = request.form.get('documents', '')
    docs = [d.strip() for d in docs_raw.split(',') if d.strip()]

    step = DemarcheStep(
        category_id=cat.id,
        title=title,
        description=desc,
        documents_needed=json.dumps(docs) if docs else '[]'
    )
    db.session.add(step)
    db.session.commit()

    flash(f"Étape '{title}' ajoutée à la catégorie '{cat.name}'", 'success')
    return redirect(url_for('admin_demarches'))

@app.route('/admin/logout')
def admin_logout():
    """Déconnexion admin"""
    session.clear()
    flash('Déconnexion admin réussie', 'info')
    return redirect(url_for('admin_login'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Servir les fichiers uploadés (protégé - admin seulement)"""
    if 'admin_id' not in session:
        flash('Accès refusé', 'error')
        return redirect(url_for('admin_login'))
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
# ============================================
# ROUTES API DASHBOARD MODERNE
# ============================================

@app.route('/api/search')
def api_search():
    """Recherche de démarches par mots-clés"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    query = request.args.get('q', '').lower()
    if not query or len(query) < 2:
        return jsonify({'results': []})

    # Rechercher dans les catégories et les étapes
    categories = DemarcheCategory.query.filter(
        DemarcheCategory.name.ilike(f'%{query}%')
    ).all()

    steps = DemarcheStep.query.filter(
        db.or_(
            DemarcheStep.title.ilike(f'%{query}%'),
            DemarcheStep.description.ilike(f'%{query}%')
        )
    ).all()

    # Formater les résultats
    results = []

    for cat in categories:
        results.append({
            'type': 'category',
            'id': cat.id,
            'name': cat.name,
            'emoji': cat.emoji,
            'description': cat.description
        })

    for step in steps:
        results.append({
            'type': 'step',
            'id': step.id,
            'title': step.title,
            'description': step.description,
            'category': step.category.name,
            'category_emoji': step.category.emoji
        })

    return jsonify({'results': results[:10]})  # Limiter à 10 résultats


@app.route('/api/progress/<int:user_id>')
def api_get_progress(user_id):
    """Récupère la progression globale d'un utilisateur"""
    if 'user_id' not in session or session['user_id'] != user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.get_or_404(user_id)

    # Récupérer toutes les étapes visibles pour ce profil
    if user.nationalite == 'fr':
        target_profiles = ['fr', 'all']
    elif user.situation == 'france':
        target_profiles = ['france', 'all']
    elif user.situation == 'algerie':
        target_profiles = ['algerie', 'all']
    else:
        target_profiles = ['all']

    categories = DemarcheCategory.query.filter(
        db.or_(
            DemarcheCategory.target_profile.in_(target_profiles),
            DemarcheCategory.target_profile == None
        )
    ).all()

    # Compter total steps et completed steps
    total_steps = 0
    completed_steps = 0

    for category in categories:
        for step in category.steps:
            total_steps += 1
            progress = UserProgress.query.filter_by(
                user_id=user_id,
                step_id=step.id,
                completed=True
            ).first()
            if progress:
                completed_steps += 1

    percentage = int((completed_steps / total_steps * 100)) if total_steps > 0 else 0

    return jsonify({
        'total_steps': total_steps,
        'completed_steps': completed_steps,
        'remaining_steps': total_steps - completed_steps,
        'percentage': percentage
    })


@app.route('/api/step/<int:step_id>/toggle', methods=['POST'])
def api_toggle_step(step_id):
    """Marque une étape comme terminée ou non terminée"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session['user_id']
    step = DemarcheStep.query.get_or_404(step_id)

    # Chercher ou créer le progress
    progress = UserProgress.query.filter_by(
        user_id=user_id,
        step_id=step_id
    ).first()

    if progress:
        # Toggle
        progress.completed = not progress.completed
        progress.completed_at = datetime.utcnow() if progress.completed else None
    else:
        # Créer nouveau
        progress = UserProgress(
            user_id=user_id,
            step_id=step_id,
            completed=True,
            completed_at=datetime.utcnow()
        )
        db.session.add(progress)

    db.session.commit()

    return jsonify({
        'success': True,
        'completed': progress.completed,
        'step_id': step_id
    })
@app.route('/api/notifications')
def api_get_notifications():
    """Récupère les notifications non lues ou récentes de l'utilisateur"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session['user_id']
    notifs = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).limit(20).all()

    results = []
    for n in notifs:
        results.append({
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'is_read': n.is_read,
            'icon': n.icon,
            'link': n.link,
            'date': n.created_at.strftime('%d/%m/%Y %H:%M')
        })

    return jsonify({
        'total': len(results),
        'unread': sum(1 for n in results if not n['is_read']),
        'notifications': results
    })

@app.route('/api/notifications/<int:notif_id>/read', methods=['POST'])
def api_read_notification(notif_id):
    """Marque une notification comme lue"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session['user_id']
    notif = Notification.query.get_or_404(notif_id)

    if notif.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    notif.is_read = True
    db.session.commit()

    return jsonify({'success': True})

@app.route('/dashboard/data')
def dashboard_data():
    """API JSON pour récupérer toutes les données du dashboard"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    
    # Déterminer le profil cible
    if user.nationalite == 'fr':
        target_profiles = ['fr', 'all']
    elif user.situation == 'france':
        target_profiles = ['france', 'all']
    elif user.situation == 'algerie':
        target_profiles = ['algerie', 'all']
    else:
        target_profiles = ['all']
    
    # Récupérer les catégories et étapes
    categories = DemarcheCategory.query.filter(
        db.or_(
            DemarcheCategory.target_profile.in_(target_profiles),
            DemarcheCategory.target_profile == None
        )
    ).order_by(DemarcheCategory.order_index).all()
    
    # Récupérer la progression de l'utilisateur
    user_progress = UserProgress.query.filter_by(user_id=user_id).all()
    progress_dict = {p.step_id: p.completed for p in user_progress}
    
    # Formater les données
    categories_data = []
    for category in categories:
        steps_data = []
        for step in sorted(category.steps, key=lambda s: s.order_index):
            steps_data.append({
                'id': step.id,
                'title': step.title,
                'description': step.description,
                'priority': step.priority,
                'completed': progress_dict.get(step.id, False),
                'documents_needed': json.loads(step.documents_needed) if step.documents_needed else [],
                'sub_steps': json.loads(step.sub_steps) if step.sub_steps else [],
                'resources': json.loads(step.resources) if step.resources else []
            })
        
        categories_data.append({
            'id': category.id,
            'name': category.name,
            'emoji': category.emoji,
            'description': category.description,
            'color': category.color,
            'steps': steps_data,
            'total_steps': len(steps_data),
            'completed_steps': sum(1 for s in steps_data if s['completed'])
        })
    
    return jsonify({
        'user': {
            'id': user.id,
            'full_name': user.full_name,
            'email': user.email,
            'nationalite': user.nationalite,
            'situation': user.situation
        },
        'categories': categories_data
    })


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("[OK] Base de donnees initialisee")
    app.run(debug=True, port=5000)