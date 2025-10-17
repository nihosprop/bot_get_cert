import logging


class GetCertFilter(logging.Filter):
    """
    Filter for logging get certificate
    """
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        return (('Выдан сертификат' in msg or 'Выдана копия' in msg) and
                record.levelno == logging.INFO)
