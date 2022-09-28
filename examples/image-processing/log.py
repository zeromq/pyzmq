import logging

logging.basicConfig(
    level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s: %(message)s'
)

logger = logging.getLogger('image-logger')

if __name__ == '__main__':
    logger.debug('... log is up ...')
