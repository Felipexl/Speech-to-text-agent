import logging
import os
import json
import datetime
from dotenv import load_dotenv
from flask import Flask, render_template_string, jsonify, request
from livekit import api
import threading
import subprocess

# Carrega variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sol-voice-app")

app = Flask(__name__)

# HTML embutido para evitar problemas de arquivo estático
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sol - Assistente de Voz</title>
    <script src="https://unpkg.com/livekit-client/dist/livekit-client.umd.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            max-width: 500px;
            width: 90%;
            text-align: center;
        }
        .logo {
            font-size: 3em;
            margin-bottom: 10px;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2em;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        .status-card {
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
            font-weight: bold;
            font-size: 1.1em;
        }
        .disconnected {
            background: #fee;
            color: #c33;
            border: 2px solid #fcc;
        }
        .connecting {
            background: #fff3cd;
            color: #856404;
            border: 2px solid #ffeaa7;
        }
        .connected {
            background: #d4edda;
            color: #155724;
            border: 2px solid #c3e6cb;
        }
        .button {
            padding: 15px 30px;
            font-size: 1.1em;
            border: none;
            border-radius: 50px;
            cursor: pointer;
            margin: 10px;
            transition: all 0.3s ease;
            font-weight: bold;
        }
        .connect-btn {
            background: linear-gradient(45deg, #4CAF50, #45a049);
            color: white;
            box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
        }
        .connect-btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
        }
        .disconnect-btn {
            background: linear-gradient(45deg, #f44336, #da190b);
            color: white;
            box-shadow: 0 4px 15px rgba(244, 67, 54, 0.3);
        }
        .disconnect-btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(244, 67, 54, 0.4);
        }
        .button:disabled {
            background: #cccccc;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        .mic-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            background: #ccc;
            border-radius: 50%;
            margin-right: 8px;
            transition: all 0.3s ease;
        }
        .mic-active {
            background: #4CAF50;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .instructions {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-top: 30px;
            text-align: left;
        }
        .instructions h3 {
            color: #333;
            margin-bottom: 15px;
        }
        .instructions ol {
            color: #666;
            line-height: 1.6;
        }
        .instructions li {
            margin-bottom: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🌟</div>
        <h1>Sol</h1>
        <p class="subtitle">Seu Assistente de Voz Inteligente</p>
        
        <button id="connect-btn" class="button connect-btn">🎤 Conectar</button>
        <button id="disconnect-btn" class="button disconnect-btn" disabled>🔌 Desconectar</button>
        
        <div id="status" class="status-card disconnected">
            <span class="mic-indicator" id="mic-indicator"></span>
            Desconectado - Clique em Conectar para começar
        </div>
        
        <div class="instructions">
            <h3>Como usar:</h3>
            <ol>
                <li>Clique em "Conectar" para iniciar</li>
                <li>Permita o acesso ao microfone</li>
                <li>Quando conectado, pode falar normalmente</li>
                <li>Sol responderá por voz automaticamente</li>
                <li>Sua conversa será transcrita e salva</li>
            </ol>
        </div>
    </div>

    <script>
        const { Room, RoomEvent, Track } = LiveKit;
        
        let room = null;
        const connectBtn = document.getElementById('connect-btn');
        const disconnectBtn = document.getElementById('disconnect-btn');
        const status = document.getElementById('status');
        const micIndicator = document.getElementById('mic-indicator');

        // Função para atualizar status
        function updateStatus(message, className) {
            status.textContent = message;
            status.className = `status-card ${className}`;
            
            if (className === 'connected') {
                micIndicator.classList.add('mic-active');
            } else {
                micIndicator.classList.remove('mic-active');
            }
        }

        connectBtn.addEventListener('click', async () => {
            try {
                updateStatus('🔄 Conectando...', 'connecting');
                connectBtn.disabled = true;

                // Obter token do servidor
                const response = await fetch('/api/token');
                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }

                room = new Room({
                    adaptiveStream: true,
                    dynacast: true,
                });
                
                // Eventos da sala
                room.on(RoomEvent.Connected, () => {
                    updateStatus('🟢 Conectado! Pode falar agora', 'connected');
                    disconnectBtn.disabled = false;
                });

                room.on(RoomEvent.Disconnected, () => {
                    updateStatus('🔴 Desconectado', 'disconnected');
                    connectBtn.disabled = false;
                    disconnectBtn.disabled = true;
                    room = null;
                });

                room.on(RoomEvent.DataReceived, (payload, participant) => {
                    // Receber mensagens do agente se necessário
                    console.log('Data received:', payload);
                });

                room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
                    if (track.kind === Track.Kind.Audio && participant.identity !== room.localParticipant.identity) {
                        // Reproduzir áudio do Sol
                        const audioElement = track.attach();
                        audioElement.autoplay = true;
                        document.body.appendChild(audioElement);
                    }
                });

                // Conectar à sala
                await room.connect(data.url, data.token);
                
                // Habilitar microfone
                await room.localParticipant.enableMicrophone(true);
                
            } catch (error) {
                console.error('Erro ao conectar:', error);
                updateStatus(`❌ Erro: ${error.message}`, 'disconnected');
                connectBtn.disabled = false;
            }
        });

        disconnectBtn.addEventListener('click', () => {
            if (room) {
                room.disconnect();
            }
        });

        // Verificar suporte do navegador
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            updateStatus('❌ Navegador não suporta microfone', 'disconnected');
            connectBtn.disabled = true;
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/token')
def get_token():
    try:
        # Verificar credenciais
        api_key = os.environ.get('LIVEKIT_API_KEY')
        api_secret = os.environ.get('LIVEKIT_API_SECRET')
        livekit_url = os.environ.get('LIVEKIT_URL')
        
        if not all([api_key, api_secret, livekit_url]):
            logger.error("Missing LiveKit credentials")
            return jsonify({'error': 'Configuração do servidor incompleta'}), 500
        
        # Gerar token único para usuário
        user_id = f"user_{os.urandom(4).hex()}"
        room_name = "sol-voice-room"
        
        token = api.AccessToken(api_key, api_secret) \
            .with_identity(user_id) \
            .with_name("Cliente") \
            .with_grants(api.VideoGrants(
                room_join=True,
                room=room_name
            ))
        
        jwt_token = token.to_jwt()
        
        logger.info(f"Token gerado para usuário {user_id} na sala {room_name}")
        
        return jsonify({
            'token': jwt_token,
            'url': livekit_url,
            'room': room_name
        })
        
    except Exception as e:
        logger.error(f"Erro ao gerar token: {e}")
        return jsonify({'error': f'Falha ao gerar token: {str(e)}'}), 500

@app.route('/api/transcripts')
def get_transcripts():
    """Endpoint para visualizar transcrições salvas"""
    try:
        transcript_files = []
        if os.path.exists('transcripts'):
            for filename in os.listdir('transcripts'):
                if filename.endswith('.json'):
                    transcript_files.append(filename)
        
        return jsonify({'files': transcript_files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    # Se não for deploy (sem RENDER env var), iniciar agente em processo separado
    if not os.environ.get('RENDER'):
        logger.info("Iniciando agente em modo local...")
        # Para deploy, o agente rodará separadamente
        
    logger.info(f"Iniciando servidor web na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False)