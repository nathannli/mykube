import logging
import sys


class Logger:
    def __init__(self):
        # Create a logger
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)  # or DEBUG for more details

        # Create handler that logs to stdout
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)

        # Optional: set a log message format
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(module)s.%(funcName)s: %(message)s"
        )
        handler.setFormatter(formatter)

        # Add the handler to the root logger
        self.logger.addHandler(handler)

        # Disable Flask's default logging to prevent duplicate logs (optional)
        logging.getLogger("werkzeug").disabled = True

    def get_logger(self):
        return self.logger


# Initialize logger instance
# logger_instance = Logger()
# logger = logger_instance.get_logger()
