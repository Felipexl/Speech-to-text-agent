import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv(override=True)

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sol-agent")

from livekit import agents
from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions
from livekit.plugins import openai, elevenlabs, silero


class SolAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
Você é a Sol, assistente virtual da Sólides, especializada em soluções de RH e gestão de pessoas.

PERSONALIDADE:
- Seja calorosa, profissional e prestativa
- Use linguagem natural e acessível
- Seja concisa mas informativa
- Mostre interesse genuíno pelas necessidades do cliente

PROTOCOLO DE ATENDIMENTO:
1. SAUDAÇÃO: Cumprimente calorosamente e se apresente. Comece com "Olá! Eu sou a Sol, a assistente virtual da Sólides. Como posso te ajudar hoje?".
2. IDENTIFICAÇÃO: Pergunte o nome, empresa e área de interesse.
3. DESCOBERTA: Faça perguntas para entender as necessidades específicas.
4. APRESENTAÇÃO: Apresente soluções relevantes da Sólides.
5. ENCAMINHAMENTO: Ofereça agendar uma reunião ou demonstração.

NOSSAS SOLUÇÕES:
- Recrutamento & Seleção: Processos eficientes para encontrar talentos.
- Gestão de Performance: Avaliações e acompanhamento de desempenho.
- Treinamento & Desenvolvimento: Capacitação e crescimento profissional.
- Consultoria em RH: Estratégias personalizadas de gestão de pessoas.
- Analytics & Relatórios: Dados inteligentes para decisões estratégicas.
- Automação de Processos: Tecnologia para otimizar tarefas de RH.

DIRETRIZES:
- Sempre responda em português brasileiro.
- Mantenha respostas curtas e diretas (1-3 frases).
- Faça uma pergunta de cada vez para manter o diálogo fluido.
- Se não souber algo, seja honesta e ofereça conectar com um especialista.
- Foque nas dores e necessidades do cliente.
- IMPORTANTE: Sempre mantenha o foco em vendas e atendimento ao cliente.
"""
        )


def validate_api_keys():
    """Valida se as chaves de API estão configuradas"""
    required_keys = {
        'OPENAI_API_KEY': 'OpenAI API Key',
        'ELEVENLABS_API_KEY': 'ElevenLabs API Key',
        'LIVEKIT_URL': 'LiveKit URL',
        'LIVEKIT_API_KEY': 'LiveKit API Key',
        'LIVEKIT_API_SECRET': 'LiveKit API Secret'
    }
    
    missing_keys = []
    for key, description in required_keys.items():
        if not os.getenv(key):
            missing_keys.append(f"{key} ({description})")
    
    if missing_keys:
        logger.error("Chaves de API ausentes:")
        for key in missing_keys:
            logger.error(f"  - {key}")
        raise ValueError("Configure as variáveis de ambiente necessárias no arquivo .env")
    
    logger.info("Todas as chaves de API estão configuradas ✓")


async def entrypoint(ctx: JobContext):
    """Função principal que inicia o agente"""
    logger.info(f"Iniciando sessão para sala: {ctx.room.name}")
    
    try:
        # Valida as chaves de API antes de iniciar
        validate_api_keys()
        
        # Conecta à sala
        await ctx.connect()
        
        # Configurações dos serviços com autenticação explícita
        openai_key = os.getenv('OPENAI_API_KEY')
        elevenlabs_key = os.getenv('ELEVENLABS_API_KEY')
        
        if not openai_key:
            raise ValueError("OPENAI_API_KEY não encontrada")
        if not elevenlabs_key:
            raise ValueError("ELEVENLABS_API_KEY não encontrada")
        
        stt = openai.STT(
            api_key=openai_key
        )
        
        llm = openai.LLM(
            model="gpt-4o",
            api_key=openai_key
        )
        
        # Configura ElevenLabs TTS com API Key explícita
        # tts = elevenlabs.TTS(
        #     api_key=elevenlabs_key
        # )
        
    # Usando o TTS da OpenAI como prova de conceito
        logger.info("Usando o TTS da OpenAI temporariamente para depuração.")
        tts = openai.TTS(
            api_key=openai_key
)

        vad = silero.VAD.load()
        
        # Cria a sessão do agente com os componentes
        session = AgentSession(
            stt=stt,
            llm=llm,
            tts=tts,
            vad=vad,
        )
        
        # Cria o assistente Sol
        assistant = SolAssistant()
        
        # Inicia a sessão
        await session.start(
            room=ctx.room,
            agent=assistant
        )
        
        # Gera saudação inicial
        await session.generate_reply(
            instructions="Cumprimente o usuário como a Sol da Sólides e ofereça ajuda."
        )
        
        logger.info("Agente Sol iniciado com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro ao iniciar o agente: {e}")
        raise


def main():
    """Função principal - nova API do LiveKit Agents"""
    try:
        # Valida configuração antes de iniciar
        validate_api_keys()
        
        # Nova forma de executar o agente usando agents.cli.run_app
        agents.cli.run_app(
            WorkerOptions(
                entrypoint_fnc=entrypoint
            )
        )
    except KeyboardInterrupt:
        logger.info("Servidor interrompido pelo usuário")
    except ValueError as e:
        logger.error(f"Erro de configuração: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        logger.error("Tente executar via CLI:")
        logger.error("python main.py dev")
        sys.exit(1)


if __name__ == "__main__":
    main()