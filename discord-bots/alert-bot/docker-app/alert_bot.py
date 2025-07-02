from flask import Flask, request
import discord
import asyncio
import os

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

client.run(bot_token)
