"""server entry"""

# -*- coding:utf-8 -*-

import sys
import os
import time
import traceback

from commonbaby.mslog import MsFileLogConfig, MsLogLevels, MsLogManager

MsLogManager.static_initial(
    dft_lvl=MsLogLevels.INFO,
    msficfg=MsFileLogConfig(fi_dir=r"./_serverlog"),
    write_to_file=True,
)
logger = MsLogManager.get_logger("idownserver")

__is_exit: bool = False
try:
    from idownserver.idownserver import DATE, VERSION, IDownServer
except Exception:
    __is_exit = True
    logger.error("Program error: {}".format(traceback.format_exc()))
    logger.error("Exist after 5s")

if __name__ == "__main__":
    server = None
    try:
        if not __is_exit:

            logger.info("idownserver start, version:{}, date:{}".format(VERSION, DATE))

            server = IDownServer()
            server.start()

            while True:
                time.sleep(1)

    except KeyboardInterrupt:
        logger.error("KeyboardInterrupted")
        time.sleep(1)
        os.kill(os.getpid(), 1)
        os._exit(1)
        sys.exit(1)
    except Exception as ex:
        try:
            logger.critical("Program error: {}".format(traceback.format_exc()))
        except Exception:
            print("Program error: {}".format(traceback.format_exc()))
    finally:
        logger.error("Program exited.....................")
        time.sleep(1)
        os.kill(os.getpid(), 1)
        os._exit(1)
        sys.exit(1)
