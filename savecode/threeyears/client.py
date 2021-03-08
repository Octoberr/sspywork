"""client entry"""

# from gevent import joinall, monkey, spawn
# monkey.patch_all(thread=False)
# monkey.patch_all()
# monkey.patch_all(socket=True,
#                  dns=True,
#                  time=False,
#                  select=False,
#                  thread=False,
#                  os=False,
#                  ssl=True,
#                  httplib=False,
#                  subprocess=False,
#                  sys=False,
#                  aggressive=False,
#                  Event=False,
#                  builtins=False,
#                  signal=False,
#                  queue=False)

import time
import traceback
import os
import sys

from commonbaby.mslog import MsLogManager, MsFileLogConfig, MsLogLevels

MsLogManager.static_initial(
    dft_lvl=MsLogLevels.DEBUG,
    msficfg=MsFileLogConfig(fi_dir="./_clientlog", max_fi_count=5),
    write_to_file=True,
)

from idownclient.idownclient import IDownClient, VERSION, DATE

logger = MsLogManager.get_logger("idownclient")

if __name__ == "__main__":
    try:
        logger.info(f"idownclient start, version:{VERSION}, date:{DATE}")
        client = IDownClient()
        client.start()

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
