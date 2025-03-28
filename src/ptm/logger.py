import os
import datetime

class PTMLogger:
    def __init__(self, level="INFO", log_handler=None):
        self.levels = ["QUIET", "DEBUG", "INFO", "WARNING", "ERROR"]
        self.level = level if level in self.levels else "INFO"
        self.log_handler = log_handler or self.default_handler

    def verbose(self, level):
        return self.levels.index(level) >= self.levels.index(self.level)

    def default_handler(self, level, *message):
        if not self.verbose(level):
            return

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {' '.join(map(str, message))}")

    def log(self, level, *message):
        self.log_handler(level, *message)

    def info(self, *message): self.log("INFO", *message)
    def debug(self, *message): self.log("DEBUG", *message)
    def warning(self, *message): self._log("WARNING", *message)
    def error(self, *message): self.log("ERROR", *message)

plog = PTMLogger(os.getenv("PTM_LOG_LEVEL", "INFO"))
