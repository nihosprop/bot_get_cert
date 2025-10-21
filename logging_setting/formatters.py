import logging
import traceback

class TelegramCompactFormatter(logging.Formatter):
    """
    Telegram compact formatter
    """
    def __init__(self, *args,
                 max_tb_lines: int = 5,
                 max_len: int = 4000,
                 **kwargs):
        """
        Initialize Telegram compact formatter.
        
        Args:
            *args: Positional arguments.
            max_tb_lines (int): Number of traceback lines to show.
            max_len (int): Maximum length of log message.
            **kwargs: Keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.max_tb_lines = max_tb_lines
        self.max_len = max_len

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record
        
        Args:
            record (logging.LogRecord): Log record.
        Returns:
            str: Formatted log record.
        """
        base = f"[{self.formatTime(record, self.datefmt)}] {record.levelname} " \
               f"{record.filename}:{record.lineno} [{record.funcName}]"

        msg = record.getMessage()

        # If there is an exception, build a summary + the last N stack lines
        if record.exc_info:
            e_type, evalue, etb = record.exc_info
            exc_name = e_type.__name__ if e_type else "Exception"
            # Full stack -> cut the last N lines (most often the "tail" is more useful)
            tb_lines = traceback.format_exception(e_type, evalue, etb)
            tail = tb_lines[-self.max_tb_lines:] if self.max_tb_lines > 0 else []
            # Let's remove unnecessary line breaks at the ends
            tail_text = "".join(tail).rstrip()
            text = f"{base} {exc_name}: {msg}\n{tail_text}"
        else:
            text = f"{base} {msg}"

        # Trimming for the Telegram limit
        if len(text) > self.max_len:
            text = text[: self.max_len - 15] + "... [truncated]"
        return text
