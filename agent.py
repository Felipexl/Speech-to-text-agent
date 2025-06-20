import logging
import datetime
import json
import os
from dotenv import load_dotenv
from livekit.agents import Agent, AgentSession, JobContext, cli, WorkerOptions
from livekit.plugins import openai, elevenlabs, silero

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sol-agent")

class SolAgent(Agent):
    def __init__(self):
        try:
            # Configurar componentes do agente
            llm = openai.LLM(model="gpt-4o")
            stt = openai.STT()  # Corrigido: era openai.LLM
            tts = elevenlabs.TTS()
            vad = silero.VAD.load()
            
            super().__init__(
                instructions="""
                Você é Sol, um assistente de vendas (SDR) especializado em atendimento.
                
                INSTRUÇÕES:
                1. Cumprimente o cliente de forma calorosa
                2. Pergunte o nome, empresa e qual é a dúvida/necessidade
                3. Responda sempre em português brasileiro
                4. Seja conciso mas amigável
                5. Faça perguntas para entender melhor a necessidade
                6. Mantenha tom profissional mas acessível
                
                EXEMPLO DE INÍCIO:
                "Olá! Eu sou a Sol, sua assistente de vendas. É um prazer falar com você! 
                Para que eu possa te ajudar melhor, pode me dizer seu nome e de qual empresa você é?"
                """,
                stt=stt,
                llm=llm,
                tts=tts,
                vad=vad,
            )
            
            self.transcript_log = []
            self.session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            logger.info("Sol Agent inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar Sol Agent: {e}")
            raise

    def save_transcript(self, speaker, text):
        """Salva transcrição em tempo real"""
        entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "speaker": speaker,
            "text": text
        }
        self.transcript_log.append(entry)
        
        # Criar pasta se não existir
        os.makedirs('transcripts', exist_ok=True)
        
        # Salvar arquivo atualizado
        filename = f"transcripts/session_{self.session_id}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({
                "session_id": self.session_id,
                "start_time": self.transcript_log[0]["timestamp"] if self.transcript_log else None,
                "transcript": self.transcript_log
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Transcrição atualizada: {filename}")

async def entrypoint(ctx: JobContext):
    try:
        logger.info(f"Conectando à sala: {ctx.room.name}")
        await ctx.connect()

        # Criar agente
        agent = SolAgent()
        
        # Iniciar sessão
        session = AgentSession()
        await session.start(room=ctx.room, agent=agent)
        
        logger.info("Sol Agent conectado e pronto para atender!")
        
    except Exception as e:
        logger.error(f"Erro no entrypoint: {e}")
        raise

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))