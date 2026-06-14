# Rapport de soutenance

## 1. Contexte et objectif

Le projet propose une mini plateforme distribuée de détection et de qualification d'e-mails de phishing. L'objectif est de montrer, dans un cadre local et pédagogique, comment plusieurs services Python peuvent coopérer pour traiter un signalement, l'analyser, le tracer et le présenter à l'utilisateur de manière sécurisée.

Le sujet est pertinent en cybersécurité car l'e-mail reste un vecteur d'attaque majeur. Les campagnes de phishing exploitent l'urgence, la pression psychologique, les faux liens, les domaines trompeurs et les pièces jointes malveillantes. Une plateforme de signalement et d'analyse permet de centraliser le traitement des alertes, de conserver un historique exploitable et d'illustrer les bonnes pratiques de sécurité applicative.

## 2. Architecture générale

La solution est organisée autour de cinq composants.

L'AuthService gère l'authentification, les rôles et les jetons JWT. Il stocke les comptes dans SQLite et utilise bcrypt pour le hash des mots de passe.

Le Gateway joue le rôle de point d'entrée REST. Il valide les requêtes, vérifie les autorisations, relaie la demande d'analyse et persiste les signalements enrichis.

L'AnalysisService expose un objet distant via Pyro5. Ce choix répond à la contrainte d'utiliser un mécanisme RPC réel, distinct des appels HTTP.

L'AuditService collecte les événements sensibles dans une base SQLite et les journalise en JSON structuré.

Le Client console permet à un utilisateur de se connecter, soumettre un e-mail suspect et consulter son historique.

Cette organisation sépare les responsabilités et permet d'illustrer une architecture distribuée sans complexité excessive.

## 3. Diagramme fonctionnel

```text
Client -> Gateway REST -> AuthService
Client -> Gateway REST -> AnalysisService (RPC Pyro5)
Gateway -> AuditService
AuthService -> AuditService
Gateway -> SQLite reports
AuthService -> SQLite users
AuditService -> SQLite logs
```

Le flux principal est le suivant : un utilisateur se connecte, obtient un JWT, soumet un e-mail suspect, le gateway valide l'entrée, appelle le moteur heuristique distant, enregistre le résultat, puis journalise l'action.

## 4. Justification des choix techniques

FastAPI a été retenu pour la simplicité de développement, la validation native avec Pydantic et la lisibilité des routes. Pour un projet universitaire, il offre un bon compromis entre sérieux industriel et rapidité de mise en œuvre.

Pyro5 a été choisi pour démontrer un vrai appel RPC entre services Python. Il est plus simple à intégrer qu'une solution gRPC complète, tout en répondant à l'exigence d'objet distant.

SQLite permet une persistance locale suffisante pour une démonstration sans infrastructure externe. Chaque service possède sa propre base pour éviter le couplage fort.

JWT convient bien à l'authentification d'une API locale. Il permet de transporter l'identité et le rôle sans maintenir une session serveur.

bcrypt est utilisé pour le hash des mots de passe car il est éprouvé, salé automatiquement et adapté au stockage des secrets.

## 5. Analyse heuristique du phishing

Le moteur d'analyse applique plusieurs règles complémentaires.

Il détecte d'abord le langage urgent ou coercitif : messages du type "immediate action required", "account suspended" ou "verify now". Ce vocabulaire est fréquent dans les attaques de phishing.

Il recherche ensuite les URLs suspectes : liens courts, adresses IP brutes, noms de domaine punycode ou structures trompeuses.

Il compare le domaine de l'expéditeur avec les domaines extraits des liens. Une incohérence forte augmente le risque, surtout lorsqu'elle est combinée à une demande de connexion ou de vérification.

Il inspecte les pièces jointes et attribue un surcoût aux extensions dangereuses comme `.exe`, `.js`, `.docm`, `.xlsm` ou `.zip`.

Le score final est ramené entre 0 et 100 et classé en trois niveaux : faible, moyen, élevé. Le service renvoie aussi une justification textuelle pour rendre la décision explicable.

## 6. Sécurité by design

Plusieurs contre-mesures sont intégrées dès la conception.

Les mots de passe ne sont jamais stockés en clair. Ils sont hashés avec bcrypt avant insertion dans la base.

Les entrées sont validées strictement. Les tailles des champs sont limitées, les champs inconnus sont refusés et les formats d'adresse ou de nom de fichier sont contrôlés.

Les erreurs côté client restent génériques. Les détails techniques sont enregistrés dans les journaux, mais ne sont pas exposés à l'utilisateur.

Les requêtes sont limitées en taille et un rate limiting simple protège le gateway contre les abus de base.

Les appels distants utilisent des timeouts, un retry simple et un circuit breaker pour réduire l'impact d'une dépendance défaillante.

Les tokens complets ne sont jamais journalisés. Seuls des aperçus tronqués peuvent être enregistrés dans des logs de diagnostic.

Les services d'audit n'acceptent que des appels internes via un en-tête partagé, ce qui évite une exposition accidentelle des journaux.

## 7. Menaces et contre-mesures

### Vol d'identifiants
Le principal risque est l'usurpation de compte. La réponse apportée est l'utilisation de bcrypt, de JWT signés et de contrôles de rôle.

### Injection de contenus malveillants
Le contenu des signalements peut être falsifié ou surdimensionné. La validation Pydantic, les limites de taille et la normalisation des champs réduisent cette surface.

### Indisponibilité d'un service
Le moteur d'analyse ou l'audit peut devenir inaccessible. Le gateway applique un retry simple et un circuit breaker pour éviter une cascade d'échecs.

### Fuite de données sensibles
Les logs ne doivent jamais contenir un jeton complet ni un mot de passe. Le format JSON structuré est utile, mais doit rester sobre et filtré.

### Abus applicatif
Un attaquant peut envoyer de nombreuses requêtes. Le rate limiting local du gateway limite l'impact d'un usage intensif.

## 8. Démonstration locale

La démonstration peut être réalisée entièrement en local.

1. Installer les dépendances.
2. Initialiser les bases avec `scripts/seed_demo.py`.
3. Lancer les quatre services.
4. Ouvrir le client console.
5. Se connecter avec le compte de démonstration.
6. Soumettre un e-mail de phishing.
7. Consulter l'historique et le détail de la décision.

Cette séquence illustre la coopération réelle entre les services et la production d'un score explicable.

## 9. Limites et évolutions possibles

La plateforme reste volontairement simple. Elle pourrait être enrichie par un stockage plus robuste, une file de messages, un moteur de règles plus avancé ou une analyse basée sur apprentissage automatique.

On pourrait également ajouter un registre de services, une authentification mutuelle entre services, un système d'alerte et un tableau de bord web.

## 10. Conclusion

Ce projet démontre une architecture distribuée réaliste en Python, centrée sur les bonnes pratiques de cybersécurité. Il combine authentification, analyse heuristique, journalisation d'audit et consultation d'historique dans une solution locale, simple à présenter et suffisamment crédible pour un projet universitaire.
