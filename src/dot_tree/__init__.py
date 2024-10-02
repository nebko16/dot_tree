import os
import logging

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
handler.setFormatter(logging.Formatter(_format))
logger.addHandler(handler)
logger.setLevel(logging.WARNING)

LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}
env_level = os.getenv('DOT_TREE_LOG_LEVEL', os.getenv('LOG_LEVEL', 'WARNING')).upper()
log_level = LOG_LEVELS.get(env_level, logging.WARNING)
logger.setLevel(log_level)

from dot_tree.classes.assets import DotTree, AppData
from dot_tree.classes.pygame import GameDotTree, GameData
from dot_tree.classes.assets import DirectoryNotEmptyError

__all__ = ['logger', 'DotTree', 'AppData', 'GameDotTree', 'GameData', 'DirectoryNotEmptyError']
