import logging

from kiwi.logger import Logger

# Initialize custom logger class for kiwi
logging.setLoggerClass(Logger)

# Set the highest log level possible as the default log level
# in the main Logger class. This is needed to allow any logfile
# handler to log all messages by default and to allow custom log
# levels per handler. Our own implementation in Logger::setLogLevel
# will then set the log level on a handler basis
logging.getLogger('kiwi').setLevel(logging.DEBUG)
