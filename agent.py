import logging
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

logger = logging.getLogger("dlai-agent")
logger.setLevel(logging.INFO)

# Configurar logs
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

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))