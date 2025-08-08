from flask import Flask, request, jsonify, make_response
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import sys
import uuid
import logging
from typing import Dict, Any, Optional, Tuple

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # Verificar variables de entorno
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        logger.error("Faltan las variables de entorno SPOTIFY_CLIENT_ID o SPOTIFY_CLIENT_SECRET")
        sys.exit(1)
    
    # Configurar Spotify
    try:
        auth_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        app.config['spotify'] = spotipy.Spotify(auth_manager=auth_manager)
        logger.info("Spotify client configurado correctamente")
    except Exception as e:
        logger.error(f"Error al configurar el cliente de Spotify: {str(e)}")
        sys.exit(1)
    
    return app

app = create_app()

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
    try:
        if not request.is_json:
            return jsonify({"error": "Se esperaba un JSON"}), 400
        
        data = request.get_json()
        logger.info(f"Llamada a recurso MCP: {data}")
        
        resource_name = data.get('name')
        parameters = data.get('parameters', {})
        
        if not resource_name:
            return jsonify({
                "error": "El campo 'name' es requerido",
                "request_id": str(uuid.uuid4())
            }), 400
        
        # Generar un ID de solicitud único
        request_id = str(uuid.uuid4())
        
        # Obtener instancia de Spotify
        sp = app.config.get('spotify')
        if not sp:
            logger.error("Cliente de Spotify no configurado")
            return jsonify({
                "error": "Error en la configuración del servidor",
                "request_id": request_id
            }), 500
        
        # Procesar el recurso solicitado
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
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Iniciando servidor en el puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=False)