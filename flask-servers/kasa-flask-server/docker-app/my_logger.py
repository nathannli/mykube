import logging
import sys
from datetime import datetime

from pytz import timezone


class Logger:
    def __init__(self, name="kasa_flask_server"):
        # Create a logger with a specific name instead of root logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)  # or DEBUG for more details
        self.tz = timezone("America/Toronto")  # UTC, America/Toronto, Europe/Berlin
        logging.Formatter.converter = self.timetz

        # Prevent duplicate handlers
        if not self.logger.handlers:
            # Create handler that logs to stdout
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)

            # Enhanced log message format with function name
            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s in %(module)s.%(funcName)s:%(lineno)d: %(message)s"
            )
            handler.setFormatter(formatter)

            # Add the handler to the logger
            self.logger.addHandler(handler)

        # Disable Flask's default logging to prevent duplicate logs (optional)
        logging.getLogger("werkzeug").disabled = True

        self.logger.info("Logger initialized")
        self.logger.info(f"Logger timezone: {self.tz.zone}")

    def get_logger(self):
        return self.logger

    def timetz(self, *args):
        return datetime.now(self.tz).timetuple()


# Initialize logger instance
# logger_instance = Logger()
# logger = logger_instance.get_logger()
