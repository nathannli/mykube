"""
Discord Alert Bot

A Flask-based web service that receives HTTP POST requests and forwards them
as messages to a specified Discord channel. The bot runs both a Flask web server
and a Discord client concurrently using threading.

Environment Variables:
    CHANNEL_ID: Discord channel ID where messages will be sent
    BOT_TOKEN: Discord bot token for authentication

Usage:
    Send POST requests to /alert endpoint with JSON payload:
    {"message": "Your alert message here"}
"""

from discord.channel import TextChannel
from __future__ import annotations
from flask import Flask, request
import discord
import asyncio
from queue import Queue, Empty
import os
import threading
import logging
from typing import Optional, Any

# Initialize Flask app and Discord client
app = Flask(__name__)
client = discord.Client(intents=discord.Intents.default())

# Message queue for thread-safe communication
alert_queue = Queue()

# Load environment variables
channel_id_str = os.getenv("CHANNEL_ID", "")
bot_token = os.getenv("BOT_TOKEN", "")

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Validate required environment variables
if channel_id_str == "" or bot_token == "":
    raise ValueError("Environment variables CHANNEL_ID and BOT_TOKEN must be set")

channel_id = int(channel_id_str)

@app.route("/alert", methods=["POST"])
def send_alert():
    """
    Flask endpoint to receive alert messages and forward them to Discord.

    Expects a POST request with JSON payload containing a 'message' field.
    The message is queued for processing by the Discord bot.

    Returns:
        tuple: Response message and HTTP status code
    """
    data: Optional[dict[str, Any]] = request.get_json()
    if not isinstance(data, dict):
        logger.error(f"Expected JSON object: {data}")
        return "Expected JSON object", 400

    message = data.get("message", "No message")
    logger.info(f"Received message: {message}")

    # Queue the message—Flask returns immediately
    alert_queue.put(message)
    return "Sent", 202


@client.event
async def on_ready():
    """
    Discord client event handler called when the bot connects.
    Starts the background alert processor task.
    """
    logger.info(f"Logged in as {client.user}")
    client.loop.create_task(process_alerts())


async def process_alerts():
    """
    Background task that processes messages from the alert queue.
    Runs continuously in the Discord bot's event loop.
    """
    await client.wait_until_ready()

    # Fetch and cache the channel once instead of on every message
    channel: TextChannel = client.get_channel(channel_id)
    if channel is None:
        logger.error(f"Channel {channel_id} not found in cache, fetching from API")
        try:
            channel = await client.fetch_channel(channel_id)
        except Exception as e:
            logger.error(f"Failed to fetch channel {channel_id}: {e}")
            return

    while not client.is_closed():
        try:
            # Non-blocking check for queued messages
            message = alert_queue.get_nowait()
            try:
                await channel.send(message)
                logger.info(f"Sent message to channel {channel_id}")
            except discord.HTTPException as e:
                logger.error(f"Discord API error sending message: {e}")
                # Re-queue the message for retry
                alert_queue.put(message)
                await asyncio.sleep(5.0)  # Back off before retrying
            except Exception as e:
                logger.error(f"Unexpected error sending message to Discord: {e}")
        except Empty:
            # Queue is empty, sleep briefly before checking again
            await asyncio.sleep(0.5)


def run_flask():
    """Run Flask web server in a separate thread."""
    app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    # Start Flask in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Run Discord bot in main thread
    client.run(bot_token)