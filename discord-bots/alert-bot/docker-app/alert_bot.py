from flask import Flask, request
import discord
import asyncio
import os
import threading

app = Flask(__name__)
client = discord.Client(intents=discord.Intents.default())
channel_id = os.getenv("CHANNEL_ID")
bot_token = os.getenv("BOT_TOKEN")

@app.route('/alert', methods=['POST'])
def send_alert():
    data = request.json
    message = data.get('message', 'No message')
    
    async def send():
        channel = client.get_channel(channel_id)
        await channel.send(message)

    asyncio.run(send())
    return 'Sent', 200

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    
def run_flask():
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    client.run(bot_token)
