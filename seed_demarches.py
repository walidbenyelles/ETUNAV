"""
Script pour peupler la base de données avec des démarches exemple
"""
import json
from app import app, db
from models import DemarcheCategory, DemarcheStep

def seed_demarches():
    """Créé des catégories et étapes de démarches pour le dashboard"""
    
    with app.app_context():
        print("🌱 Début du seeding des démarches...")
        
        # Supprimer les données existantes
        DemarcheStep.query.delete()
        DemarcheCategory.query.delete()
        db.session.commit()
        print("✓ Données existantes supprimées")
        
        # ==== CATÉGORIES ====
        
        # 1. Visa / Titre de séjour (pour Algériens en France)
        cat_visa = DemarcheCategory(
            name="Visa / Titre de séjour",
            emoji="🛂",
            description="Démarches pour obtenir et renouveler votre titre de séjour",
            color="#667eea",
            order_index=1,
            target_profile="france"  # Algériens en France
        )
        
        #2. Logement
        cat_logement = DemarcheCategory(
            name="Logement",
            emoji="🏠",
            description="Trouver, sécuriser et gérer votre logement étudiant",
            color="#f093fb",
            order_index=2,
            target_profile="all"
        )
        
        # 3. Aides Financières
        cat_aides = DemarcheCategory(
            name="Aides Financières",
            emoji="💰",
            description="Bourses, APL et aides disponibles",
            color="#4facfe",
            order_index=3,
            target_profile="all"
        )
        
        # 4. Santé & Assurance
        cat_sante = DemarcheCategory(
            name="Santé & Assurance",
            emoji="🏥",
            description="Couverture santé et assurances obligatoires",
            color="#43e97b",
            order_index=4,
            target_profile="all"
        )
        
        # 5. Banque
        cat_banque = DemarcheCategory(
            name="Banque & Paiements",
            emoji="🏦",
            description="Ouvrir un compte et gérer vos finances",
            color="#fa709a",
            order_index=5,
            target_profile="all"
        )
        
        # 6. Transports
        cat_transport = DemarcheCategory(
            name="Transports",
            emoji="🚇",
            description="Cartes de transport et réductions étudiantes",
            color="#30cfd0",
            order_index=6,
            target_profile="all"
        )
        
        # 7. Vie Sociale
        cat_social = DemarcheCategory(
            name="Vie Sociale & Loisirs",
emoji="🎉",
            description="Associations, événements et activités",
            color="#a8edea",
            order_index=7,
            target_profile="all"
        )
        
        db.session.add_all([cat_visa, cat_logement, cat_aides, cat_sante, cat_banque, cat_transport, cat_social])
        db.session.commit()
        print("✓ Catégories créées")
        
        # ==== ÉTAPES ====
        
        # VISA / TITRE DE SÉJOUR
        steps_visa = [
            DemarcheStep(
                category_id=cat_visa.id,
                title="Préparer le dossier de renouvellement",
                description="Rassemblez tous les documents nécessaires 3 mois avant l'expiration",
                priority=1,
                documents_needed=json.dumps([
                    "Attestation d'inscription universitaire",
                    "Justificatif de ressources (615€/mois minimum)",
                    "Photos d'identité récentes",
                    "Passeport valide",
                    "Justificatif de domicile"
                ]),
                sub_steps=json.dumps([
                    "Prendre contact avec votre université",
                    "Rassembler les justificatifs financiers",
                    "Faire les photos d'identité",
                    "Scanner tous vos documents"
                ]),
                resources=json.dumps([
                    {"label": "Service Public - Titre de séjour", "url": "https://www.service-public.fr/particuliers/vosdroits/F2231"},
                    {"label": "Campus France", "url": "https://www.campusfrance.org"}
                ]),
                order_index=1
            ),
            DemarcheStep(
                category_id=cat_visa.id,
                title="Prendre rendez-vous en préfecture",
                description="Réservez votre créneau en ligne ou par téléphone",
                priority=1,
                documents_needed=json.dumps([
                    "Numéro de titre de séjour actuel",
                    "Pièce d'identité"
                ]),
                sub_steps=json.dumps([
                    "Consulter le site de votre préfecture",
                    "Créer un compte si nécessaire",
                    "Choisir la date de RDV",
                    "Noter l'adresse et l'heure"
                ]),
                resources=json.dumps([
                    {"label": "Annuaire des préfectures", "url": "https://lannuaire.service-public.fr/"}
                ]),
                order_index=2
            ),
            DemarcheStep(
                category_id=cat_visa.id,
                title="Déposer la demande",
                description="Présentez-vous au rendez-vous avec votre dossier complet",
                priority=1,
                documents_needed=json.dumps([
                    "Dossier complet",
                    "Paiement (timbre fiscal)",
                    "Passeport original"
                ]),
                sub_steps=json.dumps([
                    "Vérifier tous les documents",
                    "Arriver 15 min en avance",
                    "Récupérer le récépissé",
                    "Noter la date de retrait"
                ]),
                resources=json.dumps([]),
                order_index=3
            )
        ]
        
        # LOGEMENT
        steps_logement = [
            DemarcheStep(
                category_id=cat_logement.id,
                title="Rechercher un logement",
                description="Utilisez les plateformes dédiées aux étudiants",
                priority=1,
                documents_needed=json.dumps([
                    "Pièce d'identité",
                    "Justificatif de scolarité",
                    "Garant (si nécessaire)"
                ]),
                sub_steps=json.dumps([
                    "Consulter le CROUS",
                    "Visiter les résidences privées",
                    "Comparer les prix",
                    "Vérifier la proximité des transports"
                ]),
                resources=json.dumps([
                    {"label": "CROUS", "url": "https://www.crous.fr"},
                    {"label": "Lokaviz", "url": "https://www.lokaviz.fr"},
                    {"label": "La Carte des Colocs", "url": "https://www.lacartedescolocs.fr"}
                ]),
                order_index=1
            ),
            DemarcheStep(
                category_id=cat_logement.id,
                title="Souscrire une assurance habitation",
                description="Obligatoire avant de signer le bail",
                priority=1,
                documents_needed=json.dumps([
                    "Attestation de scolarité",
                    "RIB"
                ]),
                sub_steps=json.dumps([
                    "Comparer les offres étudiantes",
                    "Souscrire en ligne",
                    "Recevoir l'attestation",
                    "Fournir au propriétaire"
                ]),
                resources=json.dumps([
                    {"label": "LMDE", "url": "https://www.lmde.fr"},
                    {"label": "SMENO", "url": "https://www.smeno.com"}
                ]),
                order_index=2
            ),
            DemarcheStep(
                category_id=cat_logement.id,
                title="Faire une demande d'APL",
                description="Aide au logement de la CAF",
                priority=2,
                documents_needed=json.dumps([
                    "Bail signé",
                    "Attestation de loyer",
                    "Justificatifs de ressources",
                    "RIB"
                ]),
                sub_steps=json.dumps([
                    "Créer un compte CAF",
                    "Faire une simulation",
                    "Déposer la demande en ligne",
                    "Envoyer les pièces justificatives"
                ]),
                resources=json.dumps([
                    {"label": "CAF - Mes Services", "url": "https://www.caf.fr"}
                ]),
                order_index=3
            )
        ]
        
        # AIDES FINANCIÈRES
        steps_aides = [
            DemarcheStep(
                category_id=cat_aides.id,
                title="Demander une bourse CROUS",
                description="Bourse sur critères sociaux",
                priority=1,
                documents_needed=json.dumps([
                    "Avis fiscal des parents",
                    "Attestation de scolarité",
                    "RIB"
                ]),
                sub_steps=json.dumps([
                    "Remplir le DSE (Dossier Social Étudiant)",
                    "Joindre les justificatifs",
                    "Attendre la réponse",
                    "Valider votre inscription"
                ]),
                resources=json.dumps([
                    {"label": "MesServices.etudiant.gouv.fr", "url": "https://www.messervices.etudiant.gouv.fr"}
                ]),
                order_index=1
            )
        ]
        
        # SANTÉ
        steps_sante = [
            DemarcheStep(
                category_id=cat_sante.id,
                title="S'affilier à la Sécurité Sociale",
                description="Couverture santé obligatoire",
                priority=1,
                documents_needed=json.dumps([
                    "Attestation de scolarité",
                    "Pièce d'identité",
                    "RIB"
                ]),
                sub_steps=json.dumps([
                    "Créer un compte Ameli",
                    "Compléter le formulaire",
                    "Recevoir votre carte Vitale"
                ]),
                resources=json.dumps([
                    {"label": "Ameli", "url": "https://www.ameli.fr"}
                ]),
                order_index=1
            ),
            DemarcheStep(
                category_id=cat_sante.id,
                title="Souscrire une mutuelle étudiante",
                description="Complémentaire santé recommandée",
                priority=2,
                documents_needed=json.dumps([
                    "Carte Vitale",
                    "Attestation de scolarité"
                ]),
                sub_steps=json.dumps([
                    "Comparer les mutuelles",
                    "Choisir une formule",
                    "Souscrire en ligne"
                ]),
                resources=json.dumps([
                    {"label": "LMDE", "url": "https://www.lmde.fr"},
                    {"label": "SMENO", "url": "https://www.smeno.com"}
                ]),
                order_index=2
            )
        ]
        
        # BANQUE
        steps_banque = [
            DemarcheStep(
                category_id=cat_banque.id,
                title="Ouvrir un compte bancaire",
                description="Compte courant avec carte bancaire",
                priority=1,
                documents_needed=json.dumps([
                    "Pièce d'identité valide",
                    "Attestation de scolarité",
                    "Justificatif de domicile"
                ]),
                sub_steps=json.dumps([
                    "Comparer les offres jeunes",
                    "Prendre RDV en agence ou en ligne",
                    "Signer le contrat",
                    "Recevoir votre carte"
                ]),
                resources=json.dumps([
                    {"label": "Comparateur bancaire", "url": "https://www.service-public.fr"}
                ]),
                order_index=1
            )
        ]
        
        # TRANSPORTS
        steps_transport = [
            DemarcheStep(
                category_id=cat_transport.id,
                title="Souscrire un abonnement transport",
                description="Pass Navigo, TBM, TCL selon votre ville",
                priority=2,
                documents_needed=json.dumps([
                    "Attestation de scolarité",
                    "Photo d'identité",
                    "Pièce d'identité"
                ]),
                sub_steps=json.dumps([
                    "Identifier le réseau de transport local",
                    "Demander le tarif étudiant",
                    "Souscrire en ligne ou en agence",
                    "Recharger votre carte"
                ]),
                resources=json.dumps([
                    {"label": "Île-de-France Mobilités", "url": "https://www.iledefrance-mobilites.fr"}
                ]),
                order_index=1
            )
        ]
        
        # VIE SOCIALE
        steps_social = [
            DemarcheStep(
                category_id=cat_social.id,
                title="Rejoindre une association étudiante",
                description="Intégrez-vous à la vie du campus",
                priority=3,
                documents_needed=json.dumps([]),
                sub_steps=json.dumps([
                    "Consulter le BDE (Bureau Des Étudiants)",
                    "Participer aux forums associatifs",
                    "Adhérer aux assos qui vous intéressent"
                ]),
                resources=json.dumps([]),
                order_index=1
            )
        ]
        
        # Ajouter toutes les étapes
        all_steps = steps_visa + steps_logement + steps_aides + steps_sante + steps_banque + steps_transport + steps_social
        db.session.add_all(all_steps)
        db.session.commit()
        print(f"✓ {len(all_steps)} étapes créées")
        
        print("\n✅ Seeding terminé avec succès!")
        print(f"  - {DemarcheCategory.query.count()} catégories")
        print(f"  - {DemarcheStep.query.count()} étapes")

if __name__ == '__main__':
    seed_demarches()
