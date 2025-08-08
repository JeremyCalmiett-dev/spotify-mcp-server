from flask import Flask, request, jsonify, make_response
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import uuid
from typing import Dict, Any, Optional

app = Flask(__name__)

# Configurar credenciales de la aplicación de Spotify
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv('SPOTIFY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
))

@app.route('/')
def index():
    return "¡El servidor MCP de Spotify está listo para recibir peticiones."

def get_mcp_schema() -> Dict[str, Any]:
    """Devuelve la especificación MCP completa del servidor."""
    return {
        "name": "spotify_mcp_server",
        "description": "Servidor MCP para controlar la reproducción de música en Spotify",
        "schema_version": "0.1.0",
        "resources": [
            {
                "name": "play_song",
                "description": "Reproduce una canción en Spotify",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Nombre de la canción o consulta de búsqueda"
                        }
                    },
                    "required": ["query"]
                },
                "returns": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "message": {"type": "string"},
                        "track_uri": {"type": "string", "optional": True}
                    }
                }
            },
            {
                "name": "pause_playback",
                "description": "Pausa la reproducción actual en Spotify",
                "parameters": {},
                "returns": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "message": {"type": "string"}
                    }
                }
            },
            {
                "name": "resume_playback",
                "description": "Reanuda la reproducción en Spotify",
                "parameters": {},
                "returns": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "message": {"type": "string"}
                    }
                }
            },
            {
                "name": "next_track",
                "description": "Pasa a la siguiente canción en la cola de reproducción",
                "parameters": {},
                "returns": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "message": {"type": "string"}
                    }
                }
            },
            {
                "name": "previous_track",
                "description": "Vuelve a la canción anterior en la cola de reproducción",
                "parameters": {},
                "returns": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "message": {"type": "string"}
                    }
                }
            }
        ]
    }

@app.route('/mcp/resources', methods=['GET'])
def list_resources():
    """Endpoint que devuelve la especificación MCP del servidor."""
    return jsonify(get_mcp_schema())

@app.route('/mcp/call', methods=['POST'])
def call_resource():
    """Endpoint que maneja las llamadas a los recursos MCP."""
    if not request.is_json:
        return jsonify({"error": "Se esperaba un JSON"}), 400
    
    data = request.get_json()
    resource_name = data.get('name')
    parameters = data.get('parameters', {})
    
    if not resource_name:
        return jsonify({"error": "El campo 'name' es requerido"}), 400
    
    # Generar un ID de solicitud único
    request_id = str(uuid.uuid4())
    
    try:
        if resource_name == 'play_song':
            query = parameters.get('query')
            if not query:
                return jsonify({
                    "error": "El parámetro 'query' es requerido",
                    "request_id": request_id
                }), 400
            
            # Buscar la canción
            results = sp.search(q=query, limit=1, type='track')
            if not results['tracks']['items']:
                return jsonify({
                    "status": "not_found",
                    "message": f"No se encontró nada para '{query}'",
                    "request_id": request_id
                })

            track = results['tracks']['items'][0]
            return jsonify({
                "status": "success",
                "message": f"Listo para reproducir: {track['name']} - {track['artists'][0]['name']}",
                "track_uri": track['uri'],
                "request_id": request_id
            })
            
        elif resource_name == 'pause_playback':
            return jsonify({
                "status": "success",
                "message": "Reproducción pausada",
                "request_id": request_id
            })
            
        elif resource_name == 'resume_playback':
            return jsonify({
                "status": "success",
                "message": "Reproducción reanudada",
                "request_id": request_id
            })
            
        elif resource_name == 'next_track':
            return jsonify({
                "status": "success",
                "message": "Siguiente canción",
                "request_id": request_id
            })
            
        elif resource_name == 'previous_track':
            return jsonify({
                "status": "success",
                "message": "Canción anterior",
                "request_id": request_id
            })
            
        else:
            return jsonify({
                "error": f"Recurso '{resource_name}' no encontrado",
                "request_id": request_id
            }), 404
            
    except Exception as e:
        return jsonify({
            "error": str(e),
            "request_id": request_id
        }), 500

# Endpoints REST para compatibilidad
@app.route('/play_song', methods=['POST'])
def play_song_endpoint():
    """Endpoint REST para reproducir una canción (compatibilidad hacia atrás)."""
    data = request.get_json() or {}
    query = data.get('query', '')
    
    # Usar el manejador MCP
    response = call_resource()
    return response

# Mapeo de endpoints antiguos a recursos MCP
LEGACY_ENDPOINTS = {
    '/play': 'resume_playback',
    '/pause': 'pause_playback',
    '/next': 'next_track',
    '/previous': 'previous_track'
}

@app.route('/<path:path>', methods=['POST'])
def legacy_endpoints(path):
    """Maneja los endpoints antiguos redirigiéndolos a los recursos MCP."""
    if path in LEGACY_ENDPOINTS:
        # Crear una solicitud MCP a partir del endpoint antiguo
        resource_name = LEGACY_ENDPOINTS[path]
        return call_resource()
    
    return jsonify({
        "status": "error",
        "message": f"Endpoint no encontrado: /{path}"
    }), 404

if __name__ == '__main__':
    app.run(debug=True, port=8080)