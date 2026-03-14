#!/usr/bin/env python3
"""
Visualiseur d'images pour Raspberry Pi avec Bottle
Version finale optimisée avec serveur Paste
"""

import os
import logging
from datetime import datetime
from bottle import Bottle, route, static_file, request, abort, response

# Réduire la verbosité des logs
logging.getLogger('paste.httpserver').setLevel(logging.WARNING)

app = Bottle()

# Configuration
IMAGE_DIR = "/config/www/captures"
SUPPORTED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')

print("CONFIG exists:", os.path.exists("/config"))
print("WWW exists:", os.path.exists("/config/www"))
print("CAPTURES:", os.listdir("/config/www"))

def get_image_files():
    """Récupère la liste des fichiers images triés par date de modification (plus récent en premier)"""
    try:
        files = []
        for filename in os.listdir(IMAGE_DIR):
            if filename.lower().endswith(SUPPORTED_EXTENSIONS):
                filepath = os.path.join(IMAGE_DIR, filename)
                if os.path.isfile(filepath):
                    mtime = os.path.getmtime(filepath)
                    files.append({
                        'name': filename,
                        'path': filepath,
                        'mtime': mtime,
                        'date': datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                    })
        
        # Trier par date de modification (plus récent en premier)
        files.sort(key=lambda x: x['mtime'], reverse=True)
        return files
    except Exception as e:
        print(f"Erreur lors de la lecture du répertoire: {e}")
        return []

def render_page(current_index, images):
    """Génère le HTML de la page avec toutes les fonctionnalités"""
    if not images:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Visualiseur d'Images</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <h1>Aucune image trouvée</h1>
            <p>Le répertoire ne contient aucune image supportée.</p>
        </body>
        </html>
        """
    base_path = request.url.rstrip('/').rsplit('/', 1)[0]
    print(f"Base path: {base_path}")
    
    current_image = images[current_index]
    total_images = len(images)
    
    # Boutons de navigation
    prev_button = ""
    if current_index < total_images - 1:
        prev_button = f'<a href="{base_path}view/{current_index + 1}" class="nav-button">← Image précédente</a>'
    else:
        prev_button = '<span class="nav-button disabled">← Image précédente</span>'
    
    next_button = ""
    if current_index > 0:
        next_button = f'<a href="{base_path}view/{current_index - 1}" class="nav-button">Image suivante →</a>'
    else:
        next_button = '<span class="nav-button disabled">Image suivante →</span>'
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Visualiseur d'Images - {current_image['name']}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            html, body {{
                height: 100%;
                margin: 0;
                background-color: #111;
                font-family: Arial, sans-serif;
            }}

            body {{
                display: flex;
                flex-direction: column;
            }}

            .container {{
                flex: 1;
                width: 100vw;
                height: 100vh;
                box-sizing: border-box;
                padding: 10px;
                background: #111;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
            }}

            .image-container {{
                margin: 20px 0;
                position: relative;
            }}
            .main-image {{
                max-width: 95vw;
                max-height: 85vh;
                object-fit: contain;
            }}
            .navigation {{
                margin: 20px 0;
                display: flex;
                justify-content: center;
                gap: 10px;
                flex-wrap: wrap;
            }}
            .nav-button {{
                padding: 10px 20px;
                background-color: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                transition: background-color 0.3s;
                display: inline-block;
                border: none;
                cursor: pointer;
                font-size: 16px;
            }}
            .nav-button:hover {{
                background-color: #0056b3;
            }}
            .nav-button.disabled {{
                background-color: #ccc;
                cursor: not-allowed;
            }}
            .info {{
                background-color: #f8f9fa;
                padding: 5px;
                border-radius: 5px;
                margin: 20px 0;
                text-align: left;
            }}
            .counter {{
                font-weight: bold;
                color: #007bff;
            }}
            @media (max-width: 768px) {{
                .navigation {{
                    flex-direction: column;
                    align-items: center;
                }}
                .nav-button {{
                    width: 80%;
                    margin: 5px 0;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Visualiseur d'Images</h1>
            
            <div class="info">
                <p><strong>Image:</strong> {current_image['name']}</p>
                <p><strong>Date:</strong> {current_image['date']}</p>
                <p class="counter">Image {current_index + 1} sur {total_images}</p>
            </div>
            
            <div class="image-container">
                <img src="{base_path}/image/{current_index}" alt="{current_image['name']}" class="main-image" id="mainImage">
            </div>
            
            <div class="navigation">
                {prev_button}
                <a href="{base_path}/" class="nav-button">🏠 Dernière image</a>
                {next_button}
            </div>
            
            <div class="navigation">
                <button onclick="refreshPage()" class="nav-button">🔄 Actualiser</button>
                <button onclick="toggleFullscreen()" class="nav-button">⛶ Plein écran</button>
                <a href="/lovelace" class="nav-button">⬅ Retour Home Assistant</a>
            </div>
        </div>
        <script>
        const BASE_PATH = window.location.pathname
            .replace(/\\/view\\/\\d+$/, '')
            .replace(/\\/$/, '');
        </script>        
        <script>
            function refreshPage() {{
                window.location.reload();
            }}
            
            function toggleFullscreen() {{
                const img = document.getElementById('mainImage');
                if (!document.fullscreenElement) {{
                    img.requestFullscreen().catch(err => {{
                        alert('Erreur plein écran: ' + err.message);
                    }});
                }} else {{
                    document.exitFullscreen();
                }}
            }}
            
            // Navigation au clavier
            document.addEventListener('keydown', function(e) {{
                switch(e.key) {{
                    case 'ArrowLeft':
                        {f"window.location.href = '{base_path}view/{current_index - 1}';" if current_index > 0 else ""}
                        break;
                    case 'ArrowRight':
                        {f"window.location.href = '{base_path}view/{current_index + 1}';" if current_index < total_images - 1 else ""}
                        break;
                    case 'Home':
                        window.location.href = '{base_path}/';
                        break;
                    case 'F5':
                        e.preventDefault();
                        refreshPage();
                        break;
                }}
            }});
        </script>
    </body>
    </html>
    """

    return html

@app.route('/')
def index():
    """Page principale - affiche la dernière image"""
    # Désactiver le cache pour cette page
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    images = get_image_files()
    return render_page(0, images)

@app.route('/view/<index:int>')
def view_image(index):
    """Affiche une image spécifique par son index"""
    # Désactiver le cache pour cette page
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    images = get_image_files()
    if not images or index < 0 or index >= len(images):
        abort(404, "Image non trouvée")
    
    return render_page(index, images)

@app.route('/image/<index:int>')
def serve_image(index):
    """Sert le fichier image par son index"""
    images = get_image_files()
    if not images or index < 0 or index >= len(images):
        abort(404, "Image non trouvée")
    
    image_file = images[index]
    
    # Ajouter un timestamp pour éviter le cache des images
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Last-Modified'] = datetime.fromtimestamp(image_file['mtime']).strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    return static_file(image_file['name'], root=IMAGE_DIR)

@app.hook('before_request')
def adjust_proxy():
    request.environ['SCRIPT_NAME'] = ''

@app.route('/api/images')
def api_images():
    """API JSON pour obtenir la liste des images"""
    images = get_image_files()
    return {'images': [{'name': img['name'], 'date': img['date']} for img in images]}

if __name__ == '__main__':
    print(f"Démarrage du visualiseur d'images...")
    print(f"Répertoire: {IMAGE_DIR}")
    
    # Vérifier que le répertoire existe
    if not os.path.exists(IMAGE_DIR):
        print(f"ERREUR: Le répertoire {IMAGE_DIR} n'existe pas!")
        exit(1)
    else:
        images = get_image_files()
        print(f"Images trouvées: {len(images)}")
        if images:
            print(f"Dernière: {images[0]['name']}")
    
    print("URL: http://localhost:8085")
    
    # Essayer Paste en premier (le plus performant)
    try:
        print("Démarrage avec Paste...")
        app.run(host='0.0.0.0', port=8085, debug=False, server='paste', quiet=True)
    except ImportError:
        print("Paste non disponible. Installation recommandée: pip install paste")
        print("Utilisation du serveur par défaut (peut être lent)...")
        app.run(host='0.0.0.0', port=8085, debug=False)
