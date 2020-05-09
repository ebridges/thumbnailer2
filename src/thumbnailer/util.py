from logging import getLogger, basicConfig, DEBUG, INFO, debug, info


DEFAULT_WIDTH = 222
DEFAULT_HEIGHT = 222


def configure_logging(verbose):
    if verbose:
        level = DEBUG
    else:
        level = INFO

    if getLogger().hasHandlers():
        # The Lambda environment pre-configures a handler logging to stderr.
        # If a handler is already configured, `.basicConfig` does not execute.
        # Thus we set the level directly.
        getLogger().setLevel(level)
    else:
        basicConfig(
            format='[%(asctime)s][%(levelname)s] %(message)s',
            datefmt='%Y/%m/%d %H:%M:%S',
            level=level,
        )
