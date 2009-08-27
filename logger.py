# Copyright (c) 2009 John (Jack) Angers, jacktasia@gmail.com
# Licensed under the terms of the MIT License (see LICENSE.txt)

import logging, logging.handlers

def yay_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = logging.handlers.RotatingFileHandler('yay.log', maxBytes=1024*1024, backupCount=20)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(asctime)s] - %(levelname)s - "%(message)s" (%(filename)s: %(funcName)s - ln%(lineno)s)', '%Y-%m-%d %a %H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger