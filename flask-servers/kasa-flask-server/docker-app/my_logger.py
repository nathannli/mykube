import logging
import sys


class Logger:
    def __init__(self, name="kasa_flask_server"):
        # Create a logger with a specific name instead of root logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)  # or DEBUG for more details

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

    def get_logger(self):
        return self.logger


# Initialize logger instance
# logger_instance = Logger()
# logger = logger_instance.get_logger()
