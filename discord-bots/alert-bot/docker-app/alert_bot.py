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

from __future__ import annotations
from flask import Flask, request
import discord
import asyncio
import os
import threading
import logging
from typing import Optional, Any

# Initialize Flask app and Discord client
app = Flask(__name__)
client = discord.Client(intents=discord.Intents.default())

# Load environment variables
channel_id_str = os.getenv("CHANNEL_ID", "")
bot_token = os.getenv("BOT_TOKEN", "")

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Validate required environment variables
if channel_id_str == "" or bot_token == "":
    raise ValueError("Environment variables CHANNEL_ID and BOT_TOKEN must be set")

# Convert channel ID to int once to avoid repeated casting
channel_id = int(channel_id_str)

@app.route("/alert", methods=["POST"])
def send_alert():
    """
    Flask endpoint to receive alert messages and forward them to Discord.

    Expects a POST request with JSON payload containing a 'message' field.
    The message is then sent to the configured Discord channel asynchronously.

    Returns:
        tuple: Response message and HTTP status code
            - ("Sent", 200) on success
            - ("Expected JSON object", 400) on invalid JSON

    Example:
        POST /alert
        Content-Type: application/json
        {"message": "Server is down!"}
    """
    # Parse JSON payload from request
    data: Optional[dict[str, Any]] = request.get_json()
    if not isinstance(data, dict):
        logger.error(f"Expected JSON object: {data}")
        return "Expected JSON object", 400

    # Extract message from payload, with fallback
    message = data.get("message", "No message")
    logger.info(f"Received message: {message}")

    async def send():
        """
        Async helper function to send message to Discord channel.

        Waits for Discord client to be ready, fetches the target channel,
        and sends the message. Handles exceptions gracefully with logging.
        """
        await client.wait_until_ready()
        try:
            # Fetch the Discord channel and send the message
            channel = await client.fetch_channel(channel_id)
            await channel.send(message)  # type: ignore
            logger.info(f"Sent message to channel {channel_id}")
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    # Schedule the async send operation on the Discord client's event loop
    asyncio.run_coroutine_threadsafe(send(), client.loop)
    return "Sent", 200

@client.event
async def on_ready():
    """
    Discord client event handler called when the bot successfully connects.

    Logs the bot's username to confirm successful authentication and connection.
    """
    logger.info(f"Logged in as {client.user}")


def run_flask():
    """
    Run the Flask web server in a separate thread.

    Starts the Flask app on all interfaces (0.0.0.0) at port 5000.
    This allows the bot to receive HTTP requests from external sources.
    """
    app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    """
    Main execution block.

    Starts both the Flask web server and Discord bot concurrently:
    1. Flask server runs in a separate thread to handle HTTP requests
    2. Discord client runs in the main thread to maintain the bot connection

    This dual-threaded approach allows the bot to simultaneously:
    - Accept HTTP POST requests via Flask
    - Maintain connection to Discord and send messages
    """
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Start Discord bot in main thread (blocking call)
    client.run(bot_token)
