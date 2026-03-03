import asyncio
import threading
import sqlite3
import datetime
from flask import Flask, request, jsonify, render_template

from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton

app = Flask(__name__)

# CONFIGURAÇÕES BOT
TELEGRAM_BOT_TOKEN = '8758772927:AAGiHm7QiZXXShfX-lBXvXMVlefWJpWermg'

# CONFIGURAÇÕES DE GRUPOS
TELEGRAM_GROUP_VIP = '-5099636662' # Você pode mudar este ID futuramente
TELEGRAM_GROUP_FREE = '-5099636662' 

# SENHA DO PAINEL (Para proteger de intrusos)
PAINEL_PASSWORD = 'kabum'

# INIT DATABASE
def init_db():
    conn = sqlite3.connect('apostas.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS apostas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_aba TEXT,
            modo_envio TEXT,
            grupo TEXT,
            tipster TEXT,
            jogo TEXT,
            mercado TEXT,
            odd TEXT,
            status TEXT DEFAULT 'Pendente',
            data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

async def async_send_telegram_message(dados):
    """Envia a aposta para o Telegram (assíncrono)."""
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    grupo_destino = TELEGRAM_GROUP_VIP if dados.get('grupo') == 'vip' else TELEGRAM_GROUP_FREE
    
    aba = dados.get('tipo_aba', 'futebol')
    modo = dados.get('modo_envio', 'completo')
    
    # Montando a mensagem bonita baseada no MODO DE ENVIO
    mensagem = ""
    
    if aba == 'futebol':
        if modo == 'resumido':
            mensagem = f"🚨 *NOVA APOSTA RÁPIDA* 🚨\n\n"
            mensagem += f"⚽ *Jogo:* {dados['jogo']}\n"
            mensagem += f"📊 *Mercado:* {dados['mercado']}\n"
            mensagem += f"🎯 *Odd:* {dados['odd']}\n\n"
            if dados.get('unidades'):
                mensagem += f"💰 *Unid:* {dados['unidades']}\n"
        else:
            # Completo
            mensagem = f"🚨 *ANALISE PREMIUM KABUM* 🚨\n\n"
            if dados.get('esporte'):
                mensagem += f"🏅 *Esporte:* {dados['esporte']}\n"
            if dados.get('competicao'):
                mensagem += f"🏆 *Comp:* {dados['competicao']}\n"
            mensagem += f"⚽ *Jogo:* {dados['jogo']}\n"
            mensagem += f"📊 *Mercado:* {dados['mercado']}\n"
            mensagem += f"🎯 *Odd:* {dados['odd']}\n"
            
            if dados.get('unidades'):
                mensagem += f"💰 *Unid:* {dados['unidades']}\n"
            if dados.get('horario'):
                mensagem += f"⏰ *Horário:* {dados['horario']}\n"
                
            if dados.get('analise'):
                mensagem += f"\n📝 *Análise do Especialista:*\n_{dados['analise']}_\n"
            
    elif aba == 'fifa':
        mensagem = f"🎮 *FIFA E-SPORTS AO VIVO* 🎮\n\n"
        if dados.get('tipo_grade_fifa'):
            casinha = "⏱️"
            if "8" in dados['tipo_grade_fifa']: casinha = "⚡"
            if "10" in dados['tipo_grade_fifa']: casinha = "🚀"
            if "12" in dados['tipo_grade_fifa']: casinha = "⏳"
            mensagem += f"{casinha} *Grade:* {dados['tipo_grade_fifa']}\n"
            
        mensagem += f"⚽ *Confronto:* {dados['jogo']}\n"
        mensagem += f"📊 *Mercado:* {dados['mercado']}\n"
        mensagem += f"🎯 *Odd:* {dados['odd']}\n"
        
        if dados.get('unidades'):
            mensagem += f"💰 *Unid:* {dados['unidades']}\n"
            
    # Assinatura do Tipster
    if dados.get('tipster') and modo != 'resumido':
        mensagem += f"\n👤 _Dica enviada por: {dados['tipster']}_\n"
    
    if aba == 'futebol' and modo == 'completo':
        mensagem += "\nBoas apostas e vamos aos greens! 🍀"

    # Criando o botão interativo
    link_final = dados.get('link', 'https://google.com')
    teclado = None
    if link_final and link_final.startswith('http'):
        botao = [[InlineKeyboardButton("🔥 APOSTAR AGORA 🔥", url=link_final)]]
        teclado = InlineKeyboardMarkup(botao)

    try:
        if dados.get('imagem') and aba != 'fifa' and modo != 'resumido':
            await bot.send_photo(chat_id=grupo_destino, photo=dados['imagem'], caption=mensagem, reply_markup=teclado, parse_mode='Markdown')
        else:
            await bot.send_message(chat_id=grupo_destino, text=mensagem, reply_markup=teclado, parse_mode='Markdown')
    except Exception as e:
        print(f"Erro gravíssimo ao enviar alerta pro Telegram: {e}")

def run_async_in_thread(dados):
    """Roda a função assíncrona do bot em uma thread separada para não travar a API do Flask."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(async_send_telegram_message(dados))
    loop.close()

def agendar_envio(minutos, dados):
    """Agenda a execução para daqui a X minutos."""
    segundos = minutos * 60
    timer = threading.Timer(segundos, run_async_in_thread, args=(dados,))
    timer.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stats', methods=['GET'])
def get_stats():
    """Retorna as estatísticas para o Dashboard V2"""
    try:
        conn = sqlite3.connect('apostas.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Últimas 15 apostas do histórico
        c.execute('SELECT * FROM apostas ORDER BY id DESC LIMIT 15')
        history_rows = c.fetchall()
        
        # Calculando métricas gerais
        c.execute("SELECT COUNT(*) FROM apostas")
        total = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM apostas WHERE status = 'Green'")
        greens = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM apostas WHERE status = 'Red'")
        reds = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM apostas WHERE status = 'Devolvido'")
        devolvidos = c.fetchone()[0]
        
        conn.close()
        
        history = [dict(ix) for ix in history_rows]
        
        validados = greens + reds
        winrate = round((greens / validados) * 100, 1) if validados > 0 else 0
        
        return jsonify({
            'success': True,
            'history': history,
            'stats': {
                'greens': greens,
                'reds': reds,
                'devolvidos': devolvidos,
                'winrate': winrate,
                'total': total
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update_result', methods=['POST'])
def update_result():
    data = request.json
    aposta_id = data.get('id')
    novo_status = data.get('status')
    
    if not aposta_id or not novo_status:
        return jsonify({'error': 'Parâmetros inválidos.'}), 400
        
    try:
        conn = sqlite3.connect('apostas.db')
        c = conn.cursor()
        c.execute('UPDATE apostas SET status = ? WHERE id = ?', (novo_status, aposta_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/bet', methods=['POST'])
def bet():
    data = request.json
    
    # 1. Checagem de Senha
    senha = data.get('senha')
    if senha != PAINEL_PASSWORD:
        return jsonify({'error': 'Senha incorreta! Acesso negado.'}), 401
        
    # 2. Validar campos obrigatórios básicos
    obrigatorios = ['jogo', 'mercado', 'odd', 'link', 'grupo', 'tipo_aba', 'modo_envio']
    for campo in obrigatorios:
        if not data.get(campo):
            return jsonify({'error': f'O campo {campo.capitalize()} é obrigatório.'}), 400
            
    # Save to Database
    try:
        conn = sqlite3.connect('apostas.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO apostas (tipo_aba, modo_envio, grupo, tipster, jogo, mercado, odd)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('tipo_aba'),
            data.get('modo_envio'),
            data.get('grupo'),
            data.get('tipster', 'Anônimo'),
            data.get('jogo'),
            data.get('mercado'),
            data.get('odd')
        ))
        conn.commit()
        conn.close()
    except Exception as db_err:
        print("Erro salvando no banco:", db_err)
        # Continua mesmo se falhar o banco, pra não quebrar a tip
            
    # 3. Lógica de Agendamento (Delay)
    minutos_agendamento = data.get('agendamento')
    try:
        minutos = int(minutos_agendamento) if minutos_agendamento else 0
    except ValueError:
        return jsonify({'error': 'Tempo de agendamento precisa ser um número inteiro.'}), 400

    try:
        if minutos > 0:
            agendar_envio(minutos, data)
            return jsonify({'success': True, 'message': f'Aposta agendada para enviar em {minutos} minutos! ⏱️'})
        else:
            # Envio Imediato usando Threading
            threading.Thread(target=run_async_in_thread, args=(data,)).start()
            return jsonify({'success': True, 'message': 'Aposta enviada com sucesso pro Telegram! 🚀'})
            
    except Exception as e:
        return jsonify({'error': f"Erro no servidor: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
