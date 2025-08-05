# Construction d'une API REST avec FastAPI pour contrôler Ansible

## 1. Objectifs

À l'issue de cette doc, vous serez capable de :
• Mettre en place un environnement Python isolé destiné au développement d'une API REST.
• Utiliser FastAPI pour exposer des endpoints HTTP asynchrones.
• Piloter des playbooks Ansible au travers d'un service web.
• Sécuriser une API (authentification par clé d'API).
• Tester l'API.

## 2. Prérequis

• Python ≥ 3.11 installé sur la machine (ou utilisation d'un conteneur Docker).
• Accès réseau permettant l'installation de packages depuis PyPI.
• Ansible et ansible-runner (ou ansible-core) installés.
• Connaissances de base en HTTP et en ligne de commande (curl/http).

## 3. Contexte du projet

Vous êtes responsable d'automatiser la gestion d'une ferme de serveurs via Ansible. Pour des besoins d'intégration dans un portail interne, vous devez exposer certaines actions ansible (exécution de playbooks, interrogation d'inventaires) au travers d'une API REST que pourra consommer le portail.

## 4. Installation et configuration

### 4.1. Cloner le projet
```bash
git clone https://github.com/anis-metref/apirest.git
cd apirest
```

### 4.2. Créer l'environnement virtuel
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 4.3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4.4. Configuration de sécurité (OBLIGATOIRE)

Créer un fichier `.env` à la racine du projet avec votre clé API :

```bash
# Créer le fichier .env
echo "API_KEY=votre-cle-secrete-ici" > .env
```

**IMPORTANT :** 
- Remplacez `votre-cle-secrete-ici` par une clé forte et unique

### 4.5. Lancer l'application
```bash
python3 main.py
```

### 4.6. Accéder à l'interface
- Interface WebSocket : `http://localhost:8000/interface`
- API REST Swagger : `http://localhost:8000/docs`
- API REST Redoc : `http://localhost:8000/redoc`

## 5. Sécurité

### 5.1. Authentification par clé API

L'API utilise une authentification par clé API pour sécuriser les endpoints sensibles :

**Endpoints libres (pas d'authentification) :**
- `GET /` - Page d'accueil
- `GET /interface` - Interface WebSocket
- `GET /docs` - Documentation Swagger

**Endpoints sécurisés (clé API requise) :**
- `GET /inventory` - Inventaire Ansible
- `POST /install-apache` - Installation Apache
- `WebSocket /ws/install-apache` - Exécution temps réel

### 5.2. Utilisation de la clé API

**Via l'interface web :**
1. Ouvrir `http://localhost:8000/interface`
2. Saisir votre clé API dans le champ sécurisé
3. Cliquer sur "Tester" pour vérifier la validité
4. Utiliser les fonctions une fois authentifié

**Via curl/API REST :**
```bash
# Avec header X-API-Key
curl -H "X-API-Key: votre-cle-secrete" http://localhost:8000/inventory

# Avec header Authorization Bearer
curl -H "Authorization: Bearer votre-cle-secrete" http://localhost:8000/inventory
```

## 6. Utilisation et tests

### 6.1. Interface WebSocket (Recommandée)
1. Ouvrir `http://localhost:8000/interface`
2. Entrer votre clé API dans le champ sécurisé
3. Cliquer sur "Tester" pour valider la clé
4. Utiliser "Installer Apache" ou "Voir Inventaire"
5. Voir l'exécution en temps réel dans la console

### 6.2. API REST
- Documentation interactive : `http://localhost:8000/docs`
- Endpoints disponibles :
  - `GET /` - Page d'accueil
  - `GET /interface` - Interface WebSocket
  - `GET /inventory` - Inventaire Ansible (SÉCURISÉ)
  - `POST /install-apache` - Installation Apache (SÉCURISÉ)
  - `WebSocket /ws/install-apache` - Exécution temps réel (SÉCURISÉ)

![endpoint](./images/1.PNG)

### 6.3. Tests via interface web
```bash
# Lancer le serveur
python3 main.py

# Ouvrir dans le navigateur
http://localhost:8000/interface
```

### 6.4. Tests via API REST sécurisée
```bash
# Vérifier l'API (libre)
curl http://localhost:8000/

# Voir l'inventaire (sécurisé)
curl -H "X-API-Key: votre-cle-secrete" http://localhost:8000/inventory

# Installer Apache (sécurisé)
curl -X POST -H "X-API-Key: votre-cle-secrete" http://localhost:8000/install-apache
```

![install-apache](./images/2.PNG)

## 7. Structure du projet
```
ansible-websocket-interface/
├── main.py                    # Application FastAPI principale
├── requirements.txt           # Dépendances Python
├── README.md                  # Documentation
├── .env                       # Configuration sécurité (à créer)
├── venv/                      # Environnement virtuel
├── static/
│   └── websocket-interface.html  # Interface web moderne
└── ansible/
    ├── inventory.yml          # Inventaire des serveurs
    └── playbooks/
        └── install-apache.yml # Playbook d'installation Apache
```

## 8. Technologies utilisées

- **FastAPI** - Framework web moderne pour Python
- **WebSocket** - Communication bidirectionnelle temps réel
- **Ansible** - Automatisation et orchestration d'infrastructure
- **ansible-runner** - Exécution programmatique d'Ansible
- **python-dotenv** - Gestion des variables d'environnement
- **HTML/CSS/JavaScript** - Interface utilisateur web moderne
- **Tailwind CSS** - Framework CSS pour l'interface
- **Python 3.11+** - Langage de programmation principal

## 9. Sécurité en production

Pour un déploiement en production :

1. **Utilisez une clé API forte** (minimum 32 caractères)
2. **Configurez HTTPS** pour chiffrer les communications
3. **Limitez l'accès réseau** aux IP autorisées
4. **Surveillez les logs** d'authentification
5. **Rotez régulièrement** la clé API
