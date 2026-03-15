#!/usr/bin/env python3
"""
Visualiseur d'images pour Raspberry Pi avec Bottle
Version finale optimisée avec serveur Paste + support Ingress HA + filtre caméra
"""

import os
import sys
import logging
from datetime import datetime
from bottle import Bottle, route, static_file, request, abort, response


# Réduire la verbosité des logs
logging.getLogger('paste.httpserver').setLevel(logging.WARNING)

sys.stdout.reconfigure(line_buffering=True)

app = Bottle()

# Configuration
IMAGE_DIR = "/share/captures"
SUPPORTED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')


def get_base_path():
    """Récupère le préfixe Ingress depuis le header X-Ingress-Path"""
    ingress_path = request.headers.get('X-Ingress-Path', '')
    if ingress_path:
        if not ingress_path.endswith('/'):
            ingress_path += '/'
        return ingress_path
    else:
        return '/'


def get_camera_list():
    """Retourne la liste des préfixes caméra détectés dans le répertoire"""
    cameras = set()
    try:
        for filename in os.listdir(IMAGE_DIR):
            if filename.lower().endswith(SUPPORTED_EXTENSIONS):
                if filename.lower().startswith('cam'):
                    prefix = ''
                    for ch in filename:
                        if ch in ('_', '-', '.', ' '):
                            break
                        prefix += ch
                    if prefix:
                        cameras.add(prefix.lower())
    except Exception as e:
        print(f"Erreur lors de la lecture des caméras: {e}")
    return sorted(cameras)


def get_image_files(camera_filter=''):
    """Récupère la liste des fichiers images triés par date de modification (plus récent en premier)"""
    try:
        files = []
        for filename in os.listdir(IMAGE_DIR):
            if filename.lower().endswith(SUPPORTED_EXTENSIONS):
                if camera_filter and not filename.lower().startswith(camera_filter.lower()):
                    continue
                filepath = os.path.join(IMAGE_DIR, filename)
                if os.path.isfile(filepath):
                    mtime = os.path.getmtime(filepath)
                    files.append({
                        'name': filename,
                        'path': filepath,
                        'mtime': mtime,
                        'date': datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                    })

        files.sort(key=lambda x: x['mtime'], reverse=True)
        return files
    except Exception as e:
        print(f"Erreur lors de la lecture du répertoire: {e}")
        return []


def render_page(current_index, images, base_path='/', camera_filter='', cameras=[]):
    """Génère le HTML de la page avec toutes les fonctionnalités"""

    filter_param = f'?cam={camera_filter}' if camera_filter else ''

    # Sélecteur de caméras
    cam_options = '<option value="">Toutes</option>'
    for cam in cameras:
        selected = 'selected' if cam == camera_filter else ''
        cam_options += f'<option value="{cam}" {selected}>{cam.upper()}</option>'

    if not images:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Visualiseur d'Images</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ background: #111; color: #eee; font-family: Arial, sans-serif;
                        display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
            </style>
        </head>
        <body>
            <div style="text-align:center">
                <h2>Aucune image trouvée</h2>
                <p>Aucune image ne correspond au filtre sélectionné.</p>
                <form method="get" action="{base_path}">
                    <select name="cam" onchange="this.form.submit()" style="padding:6px; font-size:15px; border-radius:4px;">
                        {cam_options}
                    </select>
                </form>
            </div>
        </body>
        </html>
        """

    current_image = images[current_index]
    total_images = len(images)

    # Boutons de navigation
    if current_index < total_images - 1:
        prev_button = f'<a href="{base_path}view/{current_index + 1}{filter_param}" class="nav-button">← Précédente</a>'
    else:
        prev_button = '<span class="nav-button disabled">← Précédente</span>'

    if current_index > 0:
        next_button = f'<a href="{base_path}view/{current_index - 1}{filter_param}" class="nav-button">Suivante →</a>'
    else:
        next_button = '<span class="nav-button disabled">Suivante →</span>'

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
                color: #eee;
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
                padding: 6px 10px;
                background: #111;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: flex-start;
            }}
            .header {{
                width: 100%;
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 6px;
                background: #1e1e1e;
                border-radius: 6px;
                padding: 5px 12px;
                box-sizing: border-box;
                font-size: 13px;
            }}
            .header-title {{
                font-size: 16px;
                font-weight: bold;
                color: #fff;
                white-space: nowrap;
            }}
            .header-info {{
                display: flex;
                align-items: center;
                gap: 14px;
                flex-wrap: wrap;
                font-size: 13px;
                color: #ccc;
            }}
            .header-info span {{
                white-space: nowrap;
            }}
            .counter {{
                font-weight: bold;
                color: #007bff;
            }}
            .cam-select {{
                padding: 3px 8px;
                font-size: 13px;
                border-radius: 4px;
                border: 1px solid #444;
                background: #2a2a2a;
                color: #eee;
                cursor: pointer;
            }}
            .image-container {{
                flex: 1;
                display: flex;
                align-items: center;
                justify-content: center;
                width: 100%;
                min-height: 0;
            }}
            .main-image {{
                max-width: 98vw;
                max-height: calc(100vh - 110px);
                object-fit: contain;
            }}
            .navigation {{
                margin: 6px 0;
                display: flex;
                justify-content: center;
                gap: 8px;
                flex-wrap: wrap;
            }}
            .nav-button {{
                padding: 7px 16px;
                background-color: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                transition: background-color 0.3s;
                display: inline-block;
                border: none;
                cursor: pointer;
                font-size: 14px;
            }}
            .nav-button:hover {{
                background-color: #0056b3;
            }}
            .nav-button.disabled {{
                background-color: #444;
                color: #888;
                cursor: not-allowed;
            }}
            @media (max-width: 768px) {{
                .navigation {{
                    flex-direction: column;
                    align-items: center;
                }}
                .nav-button {{
                    width: 80%;
                    margin: 3px 0;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">

            <div class="header">
                <span class="header-title">📷 Visualiseur</span>
                <div class="header-info">
                    <span><strong>{current_image['name']}</strong></span>
                    <span>{current_image['date']}</span>
                    <span class="counter">{current_index + 1} / {total_images}</span>
                    <form method="get" action="{base_path}" style="margin:0">
                        <select name="cam" class="cam-select" onchange="this.form.submit()">
                            {cam_options}
                        </select>
                    </form>
                </div>
            </div>

            <div class="image-container">
                <img src="{base_path}image/{current_index}{filter_param}" alt="{current_image['name']}" class="main-image" id="mainImage">
            </div>

            <div class="navigation">
                {prev_button}
                <a href="{base_path}{filter_param}" class="nav-button">🏠 Dernière</a>
                {next_button}
                <button onclick="refreshPage()" class="nav-button">🔄 Actualiser</button>
                <button onclick="toggleFullscreen()" class="nav-button">⛶ Plein écran</button>
            </div>

        </div>
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

            document.addEventListener('keydown', function(e) {{
                switch(e.key) {{
                    case 'ArrowLeft':
                        {f"window.location.href = '{base_path}view/{current_index - 1}{filter_param}';" if current_index > 0 else ""}
                        break;
                    case 'ArrowRight':
                        {f"window.location.href = '{base_path}view/{current_index + 1}{filter_param}';" if current_index < total_images - 1 else ""}
                        break;
                    case 'Home':
                        window.location.href = '{base_path}{filter_param}';
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
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    base_path = get_base_path()
    camera_filter = request.query.get('cam', '')
    cameras = get_camera_list()
    images = get_image_files(camera_filter)
    return render_page(0, images, base_path, camera_filter, cameras)


@app.route('/view/<index:int>')
def view_image(index):
    """Affiche une image spécifique par son index"""
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    base_path = get_base_path()
    camera_filter = request.query.get('cam', '')
    cameras = get_camera_list()
    images = get_image_files(camera_filter)
    if not images or index < 0 or index >= len(images):
        abort(404, "Image non trouvée")

    return render_page(index, images, base_path, camera_filter, cameras)


@app.route('/image/<index:int>')
def serve_image(index):
    """Sert le fichier image par son index"""
    camera_filter = request.query.get('cam', '')
    images = get_image_files(camera_filter)
    if not images or index < 0 or index >= len(images):
        abort(404, "Image non trouvée")

    image_file = images[index]

    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Last-Modified'] = datetime.fromtimestamp(image_file['mtime']).strftime('%a, %d %b %Y %H:%M:%S GMT')

    return static_file(image_file['name'], root=IMAGE_DIR)


@app.route('/api/images')
def api_images():
    """API JSON pour obtenir la liste des images"""
    camera_filter = request.query.get('cam', '')
    images = get_image_files(camera_filter)
    return {'images': [{'name': img['name'], 'date': img['date']} for img in images]}


if __name__ == '__main__':
    print(f"Démarrage du visualiseur d'images...")
    print(f"Répertoire: {IMAGE_DIR}")

    if not os.path.exists(IMAGE_DIR):
        print(f"ERREUR: Le répertoire {IMAGE_DIR} n'existe pas!")
        exit(1)
    else:
        images = get_image_files()
        print(f"Images trouvées: {len(images)}")
        if images:
            print(f"Dernière: {images[0]['name']}")
        cameras = get_camera_list()
        print(f"Caméras détectées: {cameras}")

    print("URL: http://localhost:8085")

    try:
        print("Démarrage avec Paste...")
        app.run(host='0.0.0.0', port=8085, debug=False, server='paste', quiet=True)
    except ImportError:
        print("Paste non disponible. Installation recommandée: pip install paste")
        print("Utilisation du serveur par défaut (peut être lent)...")
        app.run(host='0.0.0.0', port=8085, debug=False)