# Imports - Bibliothèques nécessaires
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os, asyncio, json, logging, ansible_runner
from datetime import datetime
import uvicorn

# Configuration logs JSON - Pour tracer les actions
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def log_json(action, status, details=None):
    """Crée des logs en format JSON pour traçabilité"""
    log_data = {"timestamp": datetime.now().isoformat(), "action": action, "status": status, "details": details or {}}
    logger.info(json.dumps(log_data))

# Création application FastAPI
app = FastAPI(title="Ansible API Simple", version="1.0.0")

# Configuration CORS pour WebSocket (support HTTP et HTTPS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "https://localhost:8000", 
        "http://127.0.0.1:8000",
        "https://127.0.0.1:8000",
        "http://0.0.0.0:8000",
        "https://0.0.0.0:8000",
        "*"  # Permet toutes les origines en développement
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Montage des fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuration chemins Ansible
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANSIBLE_DIR = os.path.join(BASE_DIR, "ansible")
INVENTORY_PATH = os.path.join(ANSIBLE_DIR, "inventory.yml")
PLAYBOOK_PATH = os.path.join(ANSIBLE_DIR, "playbooks", "install-apache.yml")

@app.get("/")
def root():
    """Page d'accueil - Redirige vers l'interface web"""
    log_json("api_access", "success", {"endpoint": "/"})
    return {"message": "API Ansible Simple - Fonctionnelle", "interface": "/interface", "api_docs": "/docs"}

@app.get("/interface", response_class=HTMLResponse)
def get_interface():
    """Interface web pour utiliser l'API Ansible"""
    log_json("interface_access", "success", {"endpoint": "/interface"})
    try:
        interface_path = os.path.join(BASE_DIR, "static", "websocket-interface.html")
        if os.path.exists(interface_path):
            with open(interface_path, 'r', encoding='utf-8') as f:
                return HTMLResponse(content=f.read())
        else:
            # Fallback vers test-websocket.html si websocket-interface.html n'existe pas
            fallback_path = os.path.join(BASE_DIR, "test-websocket.html")
            if os.path.exists(fallback_path):
                with open(fallback_path, 'r', encoding='utf-8') as f:
                    return HTMLResponse(content=f.read())
            else:
                raise HTTPException(status_code=404, detail="Interface web non trouvée")
    except Exception as e:
        log_json("interface_access", "error", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Erreur lors du chargement de l'interface: {str(e)}")

@app.get("/inventory")
def get_inventory():
    """Lit et retourne l'inventaire Ansible (liste des serveurs)"""
    try:
        if os.path.exists(INVENTORY_PATH):
            with open(INVENTORY_PATH, 'r') as f:
                content = f.read()
            log_json("inventory_read", "success", {"file": INVENTORY_PATH})
            return {"status": "success", "inventory_file": INVENTORY_PATH, "content": content}
        else:
            log_json("inventory_read", "error", {"error": "file_not_found"})
            raise HTTPException(status_code=404, detail="Inventaire non trouvé")
    except Exception as e:
        log_json("inventory_read", "error", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.post("/install-apache")
def install_apache():
    """Exécute le playbook Ansible pour installer Apache via ansible-runner"""
    log_json("apache_install", "start", {"method": "POST"})
    try:
        if not os.path.exists(PLAYBOOK_PATH):
            log_json("apache_install", "error", {"error": "playbook_not_found"})
            raise HTTPException(status_code=404, detail="Playbook non trouvé")
        
        # Exécution avec ansible-runner (API Python native)
        result = ansible_runner.run(
            playbook="install-apache.yml",
            inventory=INVENTORY_PATH,
            project_dir=os.path.join(ANSIBLE_DIR, "playbooks"),
            quiet=False
        )
        
        if result.status == "successful":
            log_json("apache_install", "success", {"job_id": str(result.config.ident)})
            return {"status": "success", "message": "Apache installé", "job_id": str(result.config.ident)}
        else:
            log_json("apache_install", "error", {"status": result.status})
            return {"status": "error", "message": f"Erreur: {result.status}", "job_id": str(result.config.ident)}
            
    except Exception as e:
        log_json("apache_install", "error", {"exception": str(e)})
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/websocket-test")
def websocket_test_page():
    """Infos pour utiliser le WebSocket (suivi temps réel)"""
    return {
        "message": "Interface WebSocket disponible",
        "websocket_url": "ws://localhost:8000/ws/install-apache",
        "instructions": ["Ouvrir test-websocket.html", "Cliquer 'Installer Apache'", "Voir en temps réel"]
    }

@app.get("/test-ws")
def test_websocket_endpoint():
    """Test endpoint pour vérifier que le serveur fonctionne"""
    return {"message": "WebSocket endpoint disponible", "url": "ws://localhost:8000/ws/install-apache"}

@app.websocket("/ws/install-apache")
async def websocket_install_apache(websocket: WebSocket):
    """WebSocket pour installation Apache en temps réel"""
    await websocket.accept()
    log_json("websocket_connect", "success", {"endpoint": "/ws/install-apache"})
    
    try:
        if not os.path.exists(PLAYBOOK_PATH):
            await websocket.send_text(json.dumps({"error": "Playbook non trouvé"}))
            return
        
        await websocket.send_text(json.dumps({"status": "start", "message": "Début installation Apache..."}))
        
        # Fonction pour exécuter ansible-runner et capturer la sortie en temps réel
        def run_ansible_with_output():
            import tempfile
            import subprocess
            import os
            
            # Commande ansible-playbook directe pour avoir la vraie sortie
            cmd = [
                "ansible-playbook", 
                "-i", INVENTORY_PATH,
                "-v",  # Verbosité pour plus de détails
                PLAYBOOK_PATH
            ]
            
            try:
                # Exécuter la commande et capturer la sortie
                process = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    cwd=os.path.join(ANSIBLE_DIR, "playbooks")
                )
                return {
                    "stdout": process.stdout,
                    "stderr": process.stderr,
                    "returncode": process.returncode
                }
            except Exception as e:
                return {
                    "stdout": "",
                    "stderr": str(e),
                    "returncode": 1
                }
        
        await websocket.send_text(json.dumps({"output": "Exécution du playbook Ansible..."}))
        
        # Exécution asynchrone
        result = await asyncio.get_event_loop().run_in_executor(None, run_ansible_with_output)
        
        # Envoyer la sortie ligne par ligne
        if result["stdout"]:
            for line in result["stdout"].split('\n'):
                if line.strip():
                    await websocket.send_text(json.dumps({"output": line}))
                    await asyncio.sleep(0.1)  # Petite pause pour simuler le temps réel
        
        if result["stderr"]:
            await websocket.send_text(json.dumps({"output": "STDERR:"}))
            for line in result["stderr"].split('\n'):
                if line.strip():
                    await websocket.send_text(json.dumps({"output": line}))
                    await asyncio.sleep(0.1)
        
        if result["returncode"] == 0:
            await websocket.send_text(json.dumps({"status": "success", "message": "Apache installé avec succès!"}))
        else:
            await websocket.send_text(json.dumps({"status": "error", "message": f"Erreur: code de retour {result['returncode']}"}))
        
        await websocket.send_text(json.dumps({"output": "Fin de l'exécution"}))
            
    except WebSocketDisconnect:
        log_json("websocket_disconnect", "info", {"endpoint": "/ws/install-apache"})
    except Exception as e:
        error_msg = f"Erreur: {str(e)}"
        log_json("websocket_error", "error", {"error": error_msg})
        try:
            await websocket.send_text(json.dumps({"error": error_msg}))
        except:
            pass

# Lancement de l'application
if __name__ == "__main__":
    """Point d'entrée - Lance le serveur FastAPI sur port 8000"""
    uvicorn.run(app, host="0.0.0.0", port=8000, ws_ping_interval=20, ws_ping_timeout=20)

