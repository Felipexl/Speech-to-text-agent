import logging
from dotenv import load_dotenv

from livekit.agents import Agent, AgentSession, JobContext
from livekit.plugins import openai, elevenlabs, silero

# Carregar variáveis de ambiente (o CLI vai precisar delas)
load_dotenv(override=True)

# Configurar o logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("course-agent")

class Assistant(Agent):
    def __init__(self) -> None:
        # Inicialização para a versão 1.0.11
        llm = openai.LLM(model="gpt-4o")
        stt = openai.STT(language="pt")
        tts = elevenlabs.TTS()
        tts = elevenlabs.TTS(voice_id="CwhRBWXzGAHq8TQ4Fs17")
        vad = silero.VAD.load()

        super().__init__(
            stt=stt,
            llm=llm,
            tts=tts,
            vad=vad,
            instructions="""
                Você é um assistente virtual prestativo e amigável que se comunica por voz.
                Sempre responda em português do Brasil, de forma clara e concisa.
            """,
        )

# A função entrypoint continua sendo a porta de entrada que o CLI vai procurar
async def entrypoint(ctx: JobContext):
    await ctx.connect()
    session = AgentSession()
    await session.start(
        room=ctx.room,
        agent=Assistant()
    )

# Note que REMOVEMOS a seção "if __name__ == '__main__':"