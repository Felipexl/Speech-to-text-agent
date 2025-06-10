import logging
import asyncio
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, jupyter
from livekit.plugins import (
    openai,
    elevenlabs,
    silero,
)
from livekit.agents.metrics import LLMMetrics, STTMetrics, TTSMetrics, EOUMetrics

# Carregar variáveis de ambiente do arquivo .env
_ = load_dotenv(override=True)

# Configurar logger
logger = logging.getLogger("dlai-agent")
logger.setLevel(logging.INFO)
# Para ver os logs no console, pode adicionar um handler:
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# Ou se preferir direcionar para um arquivo:
# handler = logging.FileHandler("agent.log")
# handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
# logger.addHandler(handler)


class MetricsAgent(Agent):
    def __init__(self) -> None:
        llm = openai.LLM(model="gpt-4o")
        # llm = openai.LLM(model="gpt-4o-mini") # Example with lower latency
        stt = openai.STT(model="whisper-1")
        tts = elevenlabs.TTS()
        silero_vad = silero.VAD.load()

        super().__init__(
            instructions="You are a helpful assistant communicating via voice",
            stt=stt,
            llm=llm,
            tts=tts,
            vad=silero_vad,
        )

        def llm_metrics_wrapper(metrics: LLMMetrics):
            asyncio.create_task(self.on_llm_metrics_collected(metrics))
        llm.on("metrics_collected", llm_metrics_wrapper)

        def stt_metrics_wrapper(metrics: STTMetrics):
            asyncio.create_task(self.on_stt_metrics_collected(metrics))
        stt.on("metrics_collected", stt_metrics_wrapper)

        def eou_metrics_wrapper(metrics: EOUMetrics):
            asyncio.create_task(self.on_eou_metrics_collected(metrics))
        stt.on("eou_metrics_collected", eou_metrics_wrapper)

        def tts_metrics_wrapper(metrics: TTSMetrics):
            asyncio.create_task(self.on_tts_metrics_collected(metrics))
        tts.on("metrics_collected", tts_metrics_wrapper)

    async def on_llm_metrics_collected(self, metrics: LLMMetrics) -> None:
        print("\n--- LLM Metrics ---")
        print(f"Prompt Tokens: {metrics.prompt_tokens}")
        print(f"Completion Tokens: {metrics.completion_tokens}")
        print(f"Tokens per second: {metrics.tokens_per_second:.4f}")
        print(f"TTFT: {metrics.ttft:.4f}s")
        print("------------------\n")

    async def on_stt_metrics_collected(self, metrics: STTMetrics) -> None:
        print("\n--- STT Metrics ---")
        print(f"Duration: {metrics.duration:.4f}s")
        print(f"Audio Duration: {metrics.audio_duration:.4f}s")
        print(f"Streamed: {'Yes' if metrics.streamed else 'No'}")
        print("------------------\n")

    async def on_eou_metrics_collected(self, metrics: EOUMetrics) -> None:
        print("\n--- End of Utterance Metrics ---")
        print(f"End of Utterance Delay: {metrics.end_of_utterance_delay:.4f}s")
        print(f"Transcription Delay: {metrics.transcription_delay:.4f}s")
        print("--------------------------------\n")

    async def on_tts_metrics_collected(self, metrics: TTSMetrics) -> None:
        print("\n--- TTS Metrics ---")
        print(f"TTFB: {metrics.ttfb:.4f}s")
        print(f"Duration: {metrics.duration:.4f}s")
        print(f"Audio Duration: {metrics.audio_duration:.4f}s")
        print(f"Streamed: {'Yes' if metrics.streamed else 'No'}")
        print("------------------\n")


async def entrypoint(ctx: JobContext):
    await ctx.connect()
    session = AgentSession()
    await session.start(
        agent=MetricsAgent(),
        room=ctx.room,
    )

if __name__ == "__main__":
    # Para rodar localmente e acessar via navegador externo:
    # 1. Certifique-se de que as variáveis de ambiente (OPENAI_API_KEY, ELEVEN_LABS_API_KEY, LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    #    estão definidas no seu arquivo .env ou no ambiente.
    # 2. O jupyter_url é opcional se o LiveKit server estiver rodando localmente e acessível.
    #    Se estiver usando um servidor LiveKit na nuvem ou diferente, ajuste a URL do jupyter_url.
    #    O URL fornecido (`https://jupyter-api-livekit.vercel.app/api/join-token`) é um helper público.
    
    # Adicionei uma configuração básica de logging para ver os outputs do logger no console.
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    # Remova o comentário da linha abaixo para executar o app.
    # jupyter.run_app(WorkerOptions(entrypoint_fnc=entrypoint), jupyter_url="https://jupyter-api-livekit.vercel.app/api/join-token")
    
    # Para rodar sem o helper do jupyter (se o senhor tiver um servidor LiveKit rodando e configurado nas variáveis de ambiente):
    # (Isto é mais avançado e pode requerer que o senhor lide com a criação da sala e tokens manualmente ou use a CLI do LiveKit)
    # Exemplo de como rodar o worker diretamente:
    # asyncio.run(agents.run_worker(WorkerOptions(entrypoint_fnc=entrypoint)))

    print("Para executar este agente, descomente uma das linhas `jupyter.run_app(...)` ou `asyncio.run(agents.run_worker(...))` no final do script.")
    print("Certifique-se de que suas variáveis de ambiente (.env) estão configuradas.")