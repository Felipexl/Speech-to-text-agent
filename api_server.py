import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from livekit import api
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Permite requisições do frontend (mesmo de um file://)
origins = ["*"] # Simplificado para desenvolvimento, pode restringir em produção
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurações centralizadas, carregadas do .env
LIVEKIT_URL = os.getenv("LIVEKIT_URL")
API_KEY = os.getenv("LIVEKIT_API_KEY")
API_SECRET = os.getenv("LIVEKIT_API_SECRET")
ROOM_NAME = "sala-sol"  # Nome da sala fixo no servidor

if not all([LIVEKIT_URL, API_KEY, API_SECRET]):
    raise EnvironmentError(
        "As variáveis de ambiente LIVEKIT_URL, LIVEKIT_API_KEY, e LIVEKIT_API_SECRET devem estar configuradas."
    )

@app.get("/get-connection-details")
async def get_connection_details(identity: str):
    """
    Endpoint que fornece TUDO que o cliente precisa para se conectar:
    - A URL do servidor WebSocket (ws_url)
    - O token de acesso JWT
    """
    try:
        token = api.AccessToken(API_KEY, API_SECRET) \
            .with_identity(identity) \
            .with_name(identity) \
            .with_grants(api.VideoGrants(
                room_join=True,
                room=ROOM_NAME, # Usa o nome da sala definido no servidor
                can_publish=True,
                can_subscribe=True,
            )) \
            .with_ttl(timedelta(hours=1))

        # Retorna um objeto JSON com a URL e o token
        return {
            "token": token.to_jwt(),
            "ws_url": LIVEKIT_URL
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    if __name__ == "__main__":
        import uvicorn
        # O Render define a variável de ambiente PORT.
        # Usamos 0.0.0.0 para que o servidor seja acessível externamente.
        port = int(os.environ.get("PORT", 8000))
        uvicorn.run("api_server:app", host="0.0.0.0", port=port, reload=False)

# Para executar: uvicorn api_server:app --reload