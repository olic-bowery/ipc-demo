import logging
import os
import sys
import time

from typing import cast, Optional

from api.util import current_time


class ToggleFormatter(logging.Formatter):
    """ Formatter that can accept records with extra=dict(bare=True) to mute the formatting prefix"""

    def __init__(self, default_formatter):
        super().__init__()
        self._default_formatter = default_formatter
        self._mute_formatter = logging.Formatter('%(message)s')

    def format(self, record):
        dir(record)
        fmt = self._mute_formatter if record.__dict__.get('bare', False) else self._default_formatter
        return fmt.format(record)


class DefaultLogger:
    __LOGGER: Optional[logging.Logger] = None

    @classmethod
    def get_log_path(cls) -> str:
        return os.environ.get('CRATE_LOG_DIR', '.log')

    @classmethod
    def get_log_filename(cls) -> str:
        return f'{current_time()}.log'

    @classmethod
    def get(cls) -> logging.Logger:
        if cls.__LOGGER is None:
            # make our log directory if it doesn't exist
            logpath = os.path.join(cls.get_log_path(), cls.get_log_filename())

            os.makedirs(os.path.dirname(logpath), exist_ok=True)

            tz = time.strftime('%z')

            file_handler = logging.FileHandler(logpath, mode="a")
            stdout_handler = logging.StreamHandler(sys.stdout)

            fmt = ToggleFormatter(logging.Formatter(
                '%(asctime)s.%(msecs)03d' + tz + ' [%(levelname)s] %(filename)s:%(funcName)s:%(lineno)d %(message)s',
                datefmt="%Y-%m-%d %T"
            ))

            file_handler.setFormatter(fmt)
            stdout_handler.setFormatter(fmt)

            logging.basicConfig(
                level=10,  # debug
                handlers=[
                    file_handler,
                    stdout_handler,
                ]
            )
            cls.__LOGGER = logging.getLogger()

        return cast(logging.Logger, cls.__LOGGER)


def get_default_logger() -> logging.Logger:
    return DefaultLogger.get()
