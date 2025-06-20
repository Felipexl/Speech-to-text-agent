import logging
import os
from dotenv import load_dotenv
import asyncio

# Carrega variáveis de ambiente
load_dotenv()

logger = logging.getLogger("dlai-agent")
logger.setLevel(logging.INFO)

# Configurar logs para produção
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

from livekit.agents import (
    Agent, 
    AgentSession, 
    JobContext, 
    cli,
    WorkerOptions
)
from livekit.plugins import openai, elevenlabs, silero
from livekit import api
from flask import Flask, send_from_directory, jsonify
import threading

class Assistant(Agent):
    def __init__(self) -> None:
        try:
            llm = openai.LLM(model="gpt-4o")
            stt = openai.STT()
            tts = elevenlabs.TTS()
            silero_vad = silero.VAD.load()

            super().__init__(
                instructions="""
                    You are a helpful assistant communicating 
                    via voice. Be concise and friendly. 
                    Respond in Portuguese if the user speaks Portuguese.
                """,
                stt=stt,
                llm=llm,
                tts=tts,
                vad=silero_vad,
            )
            logger.info("Assistant initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing assistant: {e}")
            raise

async def entrypoint(ctx: JobContext):
    try:
        logger.info(f"Connecting to room: {ctx.room.name}")
        await ctx.connect()
        
        session = AgentSession()
        await session.start(
            room=ctx.room,
            agent=Assistant()
        )
        
        logger.info("Agent session started successfully")
        
    except Exception as e:
        logger.error(f"Error in entrypoint: {e}")
        raise

# Flask app para servir a interface web e gerar tokens
app = Flask(__name__, static_folder='static')

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/token', methods=['GET'])
def get_token():
    try:
        # Verificar se as variáveis de ambiente estão configuradas
        api_key = os.environ.get('LIVEKIT_API_KEY')
        api_secret = os.environ.get('LIVEKIT_API_SECRET')
        livekit_url = os.environ.get('LIVEKIT_URL')
        
        if not all([api_key, api_secret, livekit_url]):
            logger.error("Missing LiveKit credentials")
            return jsonify({'error': 'Server configuration error'}), 500
        
        # Gerar token para o usuário se conectar
        token = api.AccessToken(api_key, api_secret) \
            .with_identity(f"user_{os.urandom(4).hex()}") \
            .with_name("User") \
            .with_grants(api.VideoGrants(
                room_join=True,
                room="voice-assistant"  # Nome fixo da sala
            ))
        
        jwt_token = token.to_jwt()
        
        logger.info(f"Token generated successfully for room: voice-assistant")
        
        return jsonify({
            'token': jwt_token,
            'url': livekit_url
        })
    except Exception as e:
        logger.error(f"Error generating token: {e}")
        return jsonify({'error': f'Failed to generate token: {str(e)}'}), 500

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)

if __name__ == "__main__":
    # Verificar se deve rodar como web server (Render) ou agent
    if os.environ.get('RENDER'):
        # No Render, roda apenas o Flask
        logger.info("Running in Render mode - Flask only")
        run_flask()
    else:
        # Localmente, roda Flask + Agent
        logger.info("Starting local development mode...")
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        
        logger.info("Starting LiveKit agent...")
        cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))