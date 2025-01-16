import os
import json
import logging
from dotenv import load_dotenv


class OsqueryLogReader:
    """
    A class for reading and processing osquery log files.
    """

    def __init__(self, logger):
        load_dotenv()
        self.log_path = os.getenv("OSQUERY_LOG_PATH")
        self.seen_events = []
        self.logger = logger
        self.run_count = 0

    def get_recent_log_events(self):
        new_events = []

        with open(self.log_path, "r", encoding="utf-8") as log_file:
            log_lines = log_file.readlines()

        for line in log_lines:
            try:
                event = json.loads(line)
                if event not in self.seen_events:
                    new_events.append(event)
                    self.seen_events.append(event)

            except json.JSONDecodeError:
                self.logger.warning("Failed to decode a log line. Skipping...")

        self.run_count += 1

        if self.run_count == 1:
            self.logger.info(
                f"Skipping {len(self.seen_events)} events already in the log file"
            )
            return []

        return new_events


def configure_logger():
    """
    Configures the logging module.
    """
    logger = logging.getLogger(__name__)

    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    script_name = os.path.basename(__file__)
    formatter = logging.Formatter(
        f"%(asctime)s - {script_name} - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger

def convert_json_to_table(json_data):
    flat_event = {}
    for key, value in json_data.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                flat_event[sub_key] = sub_value
        else:
            flat_event[key] = value

    # Determine the maximum key length
    max_key_length = max(len(key) for key in flat_event.keys())

    # Create the table header with dynamic width
    header = f"{'Key'.ljust(max_key_length)} | Value\n"
    separator = f"{'-' * max_key_length} | -----\n"
    table = header + separator

    # Add each key-value pair with consistent column width
    for key, value in flat_event.items():
        table += f"{key.ljust(max_key_length)} | {value}\n"

    return table
