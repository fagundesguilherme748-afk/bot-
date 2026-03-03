import asyncio
from telegram import Bot

# REPLACE WITH YOUR BOT TOKEN AND GROUP ID
TELEGRAM_BOT_TOKEN = '8758772927:AAGiHm7QiZXXShfX-lBXvXMVlefWJpWermg'
TELEGRAM_GROUP_ID = '-5099636662'

async def test_send():
    """Script curto para testar o envio sem precisar do HTML."""
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    mensagem = """🚨 NOVA APOSTA (TESTE)
⚽ Time A x Time B
📊 Over 1.5
🎯 Odd: 1.50
👉 https://linkdaaposta.com"""
    
    try:
        print("Enviando mensagem...")
        await bot.send_message(chat_id=TELEGRAM_GROUP_ID, text=mensagem)
        print("Mensagem de teste enviada com sucesso pro Telegram!")
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")

if __name__ == '__main__':
    asyncio.run(test_send())
