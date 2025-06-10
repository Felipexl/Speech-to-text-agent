import logging
import asyncio
from dotenv import load_dotenv

from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, run_app
from livekit.plugins import openai, elevenlabs, silero

load_dotenv(override=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])
logger = logging.getLogger("final-agent")

class Assistant(Agent):
    def __init__(self) -> None:
        llm = openai.LLM(model="gpt-4o")
        stt = openai.STT(language="pt")
        tts = elevenlabs.TTS()
        vad = silero.VAD.load()

        super().__init__(
            stt=stt, llm=llm, tts=tts, vad=vad,
            instructions="""
                Você é um assistente virtual prestativo e amigável que se comunica por voz.
                Sempre responda em português do Brasil, de forma clara e concisa.
            """,
        )

async def entrypoint(ctx: JobContext):
    await ctx.connect()
    session = AgentSession()
    await session.start(
        room=ctx.room,
        agent=Assistant()
    )

# ESTA É A PARTE QUE VOLTA
if __name__ == "__main__":
    # A função run_app deve existir nesta versão para compatibilidade com FastAPI/Uvicorn
    # Ela sabe como lidar com o worker e o servidor web.
    run_app(
        worker_options=WorkerOptions(entrypoint_fnc=entrypoint),
    )