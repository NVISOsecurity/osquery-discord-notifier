from utils.logs import OsqueryLogReader, configure_logger
from utils.bot import LogEventBot
from utils.llm import LLMAssistant

def __main__():
    logger = configure_logger()
    os_query_log_reader = OsqueryLogReader(logger)
    llm_assistant = LLMAssistant(logger)
    log_event_bot = LogEventBot(logger, os_query_log_reader, llm_assistant)
    log_event_bot.run()


if __name__ == "__main__":
    __main__()
