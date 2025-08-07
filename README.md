# Servidor MCP para Spotify

Este proyecto es un servidor MCP (Model Context Protocol) que permite a un agente de IA como Cascade interactuar con la API de Spotify.

## Configuración

1.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configurar credenciales:**
    - Renombra o copia el archivo `.env.example` a `.env`.
    - Abre el archivo `.env` y reemplaza los valores `TU_CLIENT_ID_DE_SPOTIFY_AQUI` y `TU_CLIENT_SECRET_DE_SPOTIFY_AQUI` con tus credenciales del [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).

3.  **Ejecutar el servidor:**
    ```bash
    flask run
    ```

El servidor se ejecutará en `http://127.0.0.1:5000`.
