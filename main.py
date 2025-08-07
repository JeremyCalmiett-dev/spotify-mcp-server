from flask import Flask, request, jsonify
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

app = Flask(__name__)

# Configurar credenciales de la aplicación de Spotify
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv('SPOTIFY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
))

@app.route('/')
def index():
    return "¡El servidor MCP de Spotify está listo para recibir peticiones."

@app.route('/mcp/resources', methods=['GET'])
def list_resources():
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
            # En un entorno real, aquí se usaría el SDK de Web Playback de Spotify
            return jsonify({
                "status": "success",
                "message": f"Listo para reproducir: {results['tracks']['items'][0]['name']}",
                "track_uri": track_uri
            })

        elif resource_name == 'get_current_song':
            # En un entorno real, esto se conectaría al reproductor del usuario
            return jsonify({
                "status": "success",
                "message": "Esta funcionalidad requiere autenticación del usuario."
            })

        else:
            return jsonify({"error": f"Recurso '{resource_name}' no encontrado."}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoints adicionales para control de reproducción
@app.route('/play', methods=['POST'])
def play():
    return jsonify({"status": "success", "message": "Reproducción iniciada"})

@app.route('/pause', methods=['POST'])
def pause():
    return jsonify({"status": "success", "message": "Reproducción pausada"})

@app.route('/next', methods=['POST'])
def next_track():
    return jsonify({"status": "success", "message": "Siguiente canción"})

@app.route('/previous', methods=['POST'])
def previous_track():
    return jsonify({"status": "success", "message": "Canción anterior"})

@app.route('/play_song', methods=['POST'])
def play_song():
    data = request.json
    query = data.get('query', '')
    return jsonify({
        "status": "success",
        "message": f"Buscando: {query}",
        "query": query
    })

if __name__ == '__main__':
    app.run(debug=True, port=8080)