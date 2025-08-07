import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24) # Clave secreta para la sesión de Flask

# Ámbito de permisos que nuestra app solicitará a Spotify
SCOPE = "user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private"

# Configuración de cache para el token de autenticación
# Esto crea un archivo .cache en el directorio para guardar el token
cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)

# Objeto de autenticación de Spotipy
auth_manager = SpotifyOAuth(
    scope=SCOPE,
    cache_handler=cache_handler,
    show_dialog=True # Muestra el diálogo de autorización de Spotify cada vez
)

@app.route('/')
def index():
    # Si no estamos autenticados, redirigir a la página de login
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        auth_url = auth_manager.get_authorize_url()
        return f'<h2>Necesitas autenticarte con Spotify</h2><a href="{auth_url}">Login</a>'

    return "¡Autenticado! El servidor MCP de Spotify está listo para recibir peticiones."

@app.route('/callback')
def callback():
    # Cuando Spotify redirige de vuelta, obtenemos el token de acceso
    auth_manager.get_access_token(request.args.get("code"))
    return redirect(url_for('index'))

@app.route('/mcp/resources', methods=['GET'])
def list_resources():
    # Aquí es donde definimos las "herramientas" que la IA puede usar
    resources = {
        "resources": [
            {
                "name": "play_music",
                "description": "Reproduce música en Spotify. Puede ser una canción, artista o álbum.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "La canción, artista o álbum a buscar y reproducir."}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_current_song",
                "description": "Obtiene la canción que se está reproduciendo actualmente en Spotify.",
                "parameters": {}
            }
        ]
    }
    return jsonify(resources)

@app.route('/mcp/call', methods=['POST'])
def call_resource():
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return jsonify({"error": "Not authenticated"}), 401

    # Crear un cliente de Spotipy con el token de autenticación
    sp = spotipy.Spotify(auth_manager=auth_manager)
    
    data = request.json
    resource_name = data.get('resource')
    params = data.get('parameters', {})

    try:
        if resource_name == 'play_music':
            query = params.get('query')
            if not query:
                return jsonify({"error": "El parámetro 'query' es requerido."}), 400
            
            # Buscar la canción
            results = sp.search(q=query, limit=1, type='track')
            if not results['tracks']['items']:
                return jsonify({"status": f"No se encontró nada para '{query}'"})

            track_uri = results['tracks']['items'][0]['uri']
            sp.start_playback(uris=[track_uri])
            return jsonify({"status": f"Reproduciendo: {results['tracks']['items'][0]['name']}"})

        elif resource_name == 'get_current_song':
            track_info = sp.current_playback()
            if track_info and track_info['is_playing']:
                song_name = track_info['item']['name']
                artist_name = track_info['item']['artists'][0]['name']
                return jsonify({"currently_playing": f"{song_name} por {artist_name}"})
            else:
                return jsonify({"currently_playing": "No hay nada reproduciéndose."})

        else:
            return jsonify({"error": f"Recurso '{resource_name}' no encontrado."}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Usamos el puerto 5000 por defecto
    app.run(debug=True, port=8080)
