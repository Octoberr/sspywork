"""zgrab scanner"""

# -*- coding:utf-8 -*-

import os
import re
import threading
import traceback

from commonbaby.helpers.helper_str import is_none_or_white_space

from datacontract.iscoutdataset import IscoutTask
from .zgrab2config import Zgrab2Config
from .zgrab2scanner.zgrab2scannerftp import Zgrab2ScannerFtp
from .zgrab2scanner.zgrab2scannerhttp import Zgrab2ScannerHttp
from .zgrab2scanner.zgrab2scannermongodb import Zgrab2ScannerMongodb
from .zgrab2scanner.zgrab2scannermssql import Zgrab2ScannerMssql
from .zgrab2scanner.zgrab2scannerntp import Zgrab2ScannerNtp
from .zgrab2scanner.zgrab2scannerredis import Zgrab2ScannerRedis
from .zgrab2scanner.zgrab2scannerssh import Zgrab2ScannerSsh
from .zgrab2scanner.zgrab2scannermssql import Zgrab2ScannerMssql
from .zgrab2scanner.zgrab2scannerftp import Zgrab2ScannerFtp
from .zgrab2scanner.zgrab2scannersmtp import Zgrab2ScannerSMTP
from .zgrab2scanner.zgrab2scannertelnet import Zgrab2ScannerTelnet
from .zgrab2scanner.zgrab2scannertls import Zgrab2ScannerTls
from .zgrab2scanner.zgrab2scannerimap import Zgrab2ScannerImap
from .zgrab2scanner.zgrab2scannerpop3 import Zgrab2ScannerPop3
from .zgrab2scanner.zgrab2scannermysql import Zgrab2ScannerMysql
from .zgrab2scanner.zgrab2scanneroracle import Zgrab2ScannerOracle
from ..scantoolbase import ScanToolBase
from ....clientdatafeedback.scoutdatafeedback import PortInfo
# from ....config_scanner import zgrab2config


class Zgrab2(ScanToolBase):
    """zgrab scanner"""

    _is_zgrab_found = False
    _init_locker = threading.Lock()

    _zgrab2_may_path: list = [
        "zgrab2",
        "/usr/bin/zgrab2",
        "/usr/local/bin/zgrab2",
        "/sw/bin/zgrab2",
        "/opt/local/bin/zgrab2",
    ]
    _zgrab_path = "zgrab2"

    _re_version = re.compile("ss")

    _zgrab_version = None
    _zgrab_subversion = None

    def __init__(self):
        ScanToolBase.__init__(self, "zgrab2")
        # self._config: Zgrab2Config = zgrab2config
        self._config: Zgrab2Config = None
        if not isinstance(self._config, Zgrab2Config):
            self._config = Zgrab2Config()

        for zgpath in self._config.zgrab2path:
            if not zgpath in Zgrab2._zgrab2_may_path:
                Zgrab2._zgrab2_may_path.append(zgpath)

        # check zgrab2
        self._init_zgrab2()
        # init scanners
        self._scanner_tls: Zgrab2ScannerTls = Zgrab2ScannerTls(Zgrab2._zgrab_path)
        self._scanner_http: Zgrab2ScannerHttp = Zgrab2ScannerHttp(Zgrab2._zgrab_path)
        self._scanner_ssh: Zgrab2ScannerSsh = Zgrab2ScannerSsh(Zgrab2._zgrab_path)
        self._scanner_mongodb: Zgrab2ScannerMongodb = Zgrab2ScannerMongodb(
            Zgrab2._zgrab_path
        )
        self._scanner_redis: Zgrab2ScannerRedis = Zgrab2ScannerRedis(Zgrab2._zgrab_path)
        self._scanner_telnet: Zgrab2ScannerTelnet = Zgrab2ScannerTelnet(
            Zgrab2._zgrab_path
        )
        self._scanner_mssql: Zgrab2ScannerMssql = Zgrab2ScannerMssql(Zgrab2._zgrab_path)
        self._scanner_ftp: Zgrab2ScannerFtp = Zgrab2ScannerFtp(Zgrab2._zgrab_path)
        self._scanner_smtp: Zgrab2ScannerSMTP = Zgrab2ScannerSMTP(Zgrab2._zgrab_path)
        self._scanner_ntp: Zgrab2ScannerNtp = Zgrab2ScannerNtp(Zgrab2._zgrab_path)
        self._scanner_imap: Zgrab2ScannerImap = Zgrab2ScannerImap(Zgrab2._zgrab_path)
        self._scanner_pop3: Zgrab2ScannerPop3 = Zgrab2ScannerPop3(Zgrab2._zgrab_path)
        self._scanner_mysql: Zgrab2ScannerMysql = Zgrab2ScannerMysql(Zgrab2._zgrab_path)
        self._scanner_oracle: Zgrab2ScannerOracle = Zgrab2ScannerOracle(
            Zgrab2._zgrab_path
        )

    def _init_zgrab2(self):
        """check zgrab2 installation, if not found, raise exception"""
        try:
            if Zgrab2._is_zgrab_found:
                return

            with Zgrab2._init_locker:
                if Zgrab2._is_zgrab_found:
                    return

                # call  'zgrab --input-file=./test.csv --outputfile=./test.json --port 443 --tls --http="/"'
                # 'github.com' is in test.csv

                # create a test.csv
                test_csv_dir = os.path.join(self._tmpdir, "test")
                if not os.path.exists(test_csv_dir):
                    os.makedirs(test_csv_dir)
                test_csv_path = os.path.join(test_csv_dir, "test.csv")
                if os.path.exists(test_csv_path):
                    os.remove(test_csv_path)
                with open(test_csv_path, mode="w", encoding="utf-8") as fstest:
                    fstest.write("api.github.com\n")
                # zgrab2 http --port=443 --timeout=0 --session-ticket
                # #--user-agent="Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)
                # #Chrome/65.0.3325.181 Safari/537.36" --retry-https --use-https -f test.csv -o test.json
                for zpath in Zgrab2._zgrab2_may_path:
                    try:
                        p = self._run_process(
                            zpath,
                            *[
                                "http",
                                "--port=443",
                                '--endpoint="/"',
                                "--use-https",
                                '--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36"',
                                "--input-file=./test.csv",
                                "--output-file=./test.json",
                            ],
                            sudo=self._config.sudo,
                            rootDir=test_csv_dir,
                        )
                    except Exception as ex:
                        self._logger.debug("Zgrab not found in '%s'" % zpath)
                    else:
                        output, error, notfound = super(Zgrab2, self)._is_cmd_not_found(
                            p
                        )
                        if notfound:
                            continue
                        if not is_none_or_white_space(output):
                            self._logger.info(output)
                        if not is_none_or_white_space(error):
                            self._logger.info(error)
                        Zgrab2._zgrab_path = zpath  # save path
                        break
                    finally:
                        if not p is None:
                            p.kill()
                else:
                    raise Exception(
                        "zgrab program was not found in path. PATH is : {0}".format(
                            os.getenv("PATH")
                        )
                    )

                sig = "finished grab"  # 'banner-grab: finished grab'
                if sig in output or sig in error:
                    Zgrab2._is_zgrab_found = True

                if not Zgrab2._is_zgrab_found:
                    raise EnvironmentError(
                        "zgrab program was not found in path: %s" % error
                    )

        except Exception as ex:
            raise ex

    #############################

    def get_tlsinfo(self, task: IscoutTask, level, portinfo: PortInfo, *args) -> iter:
        """scan http services and get the banner"""
        try:
            self._scanner_tls.get_banner_tls(
                task,
                level,
                portinfo,
                *args,
                zgrab2path=self._zgrab_path,
                sudo=self._config.sudo,
                timeout=self._config.timeout,
            )
        except Exception:
            self._logger.error(
                "Scan http error:\ntaskid:{}\batchid:{}\nlevel:{}\nhost:{}\nerror:{}".format(
                    task.taskid,
                    task.batchid,
                    level,
                    portinfo._host,
                    traceback.format_exc(),
                )
            )

    def get_siteinfo(self, task: IscoutTask, level, portinfo: PortInfo, *args) -> iter:
        """scan http services and get the banner"""
        try:
            self._scanner_http.get_banner_http(
                task,
                level,
                portinfo,
                *args,
                zgrab2path=self._zgrab_path,
                sudo=self._config.sudo,
                timeout=self._config.timeout,
            )

        except Exception:
            self._logger.error(
                "Scan http error:\ntaskid:{}\batchid:{}\nlevel:{}\nhost:{}\nerror:{}".format(
                    task.taskid,
                    task.batchid,
                    level,
                    portinfo._host,
                    traceback.format_exc(),
                )
            )

    def get_ssh_info(
        self, task: IscoutTask, level: int, portinfo: PortInfo, *args
    ) -> iter:
        """get ssh info"""
        try:
            self._scanner_ssh.get_banner(
                task,
                level,
                portinfo,
                *args,
                zgrab2path=self._zgrab_path,
                sudo=self._config.sudo,
                timeout=self._config.timeout,
            )
        except Exception:
            self._logger.error(
                "Scan ssh error:\ntaskid:{}\batchid:{}\nlevel:{}\nhost:{}\nerror:{}".format(
                    task.taskid,
                    task.batchid,
                    level,
                    portinfo._host,
                    traceback.format_exc(),
                )
            )

    def get_mongodb_info(
        self, task: IscoutTask, level: int, portinfo: PortInfo, *args
    ) -> iter:
        """get mongodb info"""
        try:
            self._scanner_mongodb.get_banner_mongodb(
                task,
                level,
                portinfo,
                *args,
                zgrab2path=self._zgrab_path,
                sudo=self._config.sudo,
                timeout=self._config.timeout,
            )
        except Exception:
            self._logger.error(
                "Scan mongodb error:\ntaskid:{}\batchid:{}\nlevel:{}\nhost:{}\nerror:{}".format(
                    task.taskid,
                    task.batchid,
                    level,
                    portinfo._host,
                    traceback.format_exc(),
                )
            )

    def get_redis_info(
        self, task: IscoutTask, level: int, portinfo: PortInfo, *args
    ) -> iter:
        """get redis info"""
        try:
            self._scanner_redis.get_banner_redis(
                task,
                level,
                portinfo,
                *args,
                zgrab2path=self._zgrab_path,
                sudo=self._config.sudo,
                timeout=self._config.timeout,
            )
        except Exception:
            self._logger.error(
                "Scan redis error:\ntaskid:{}\batchid:{}\nlevel:{}\nhost:{}\nerror:{}".format(
                    task.taskid,
                    task.batchid,
                    level,
                    portinfo._host,
                    traceback.format_exc(),
                )
            )

    def get_telnet_info(
        self, task: IscoutTask, level: int, portinfo: PortInfo, *args
    ) -> iter:
        """get telnet info"""
        try:
            self._scanner_telnet.get_banner_telnet(
                task,
                level,
                portinfo,
                *args,
                zgrab2path=self._zgrab_path,
                sudo=self._config.sudo,
                timeout=self._config.timeout,
            )
        except Exception:
            self._logger.error(
                "Scan telnet error:\ntaskid:{}\batchid:{}\nlevel:{}\nhost:{}\nerror:{}".format(
                    task.taskid,
                    task.batchid,
                    level,
                    portinfo._host,
                    traceback.format_exc(),
                )
            )

    def get_mssql_info(
        self, task: IscoutTask, level: int, portinfo: PortInfo, *args
    ) -> iter:
        """get mssql info"""
        try:
            self._scanner_mssql.get_banner_mssql(
                task,
                level,
                portinfo,
                *args,
                zgrab2path=self._zgrab_path,
                sudo=self._config.sudo,
                timeout=self._config.timeout,
            )
        except Exception:
            self._logger.error(
                "Scan mssql error:\ntaskid:{}\batchid:{}\nlevel:{}\nhost:{}\nerror:{}".format(
                    task.taskid,
                    task.batchid,
                    level,
                    portinfo._host,
                    traceback.format_exc(),
                )
            )

    def get_ftp_info(
        self, task: IscoutTask, level: int, portinfo: PortInfo, *args
    ) -> iter:
        """get ftp info"""
        try:
            self._scanner_ftp.get_banner_ftp(
                task,
                level,
                portinfo,
                *args,
                zgrab2path=self._zgrab_path,
                sudo=self._config.sudo,
                timeout=self._config.timeout,
            )
        except Exception:
            self._logger.error(
                "Scan ftp error:\ntaskid:{}\batchid:{}\nlevel:{}\nhost:{}\nerror:{}".format(
                    task.taskid,
                    task.batchid,
                    level,
                    portinfo._host,
                    traceback.format_exc(),
                )
            )

    def get_smtp_info(
        self, task: IscoutTask, level: int, portinfo: PortInfo, *args
    ) -> iter:
        """get ftp info"""
        try:
            self._scanner_smtp.get_banner_smtp(
                task,
                level,
                portinfo,
                *args,
                zgrab2path=self._zgrab_path,
                sudo=self._config.sudo,
                timeout=self._config.timeout,
            )
        except Exception:
            self._logger.error(
                "Scan smtp error:\ntaskid:{}\batchid:{}\nlevel:{}\nhost:{}\nerror:{}".format(
                    task.taskid,
                    task.batchid,
                    level,
                    portinfo._host,
                    traceback.format_exc(),
                )
            )

    def get_ntp_info(
        self, task: IscoutTask, level: int, portinfo: PortInfo, *args
    ) -> iter:
        """get ntp info"""
        try:
            self._scanner_ntp.get_banner_ntp(
                task,
                level,
                portinfo,
                *args,
                zgrab2path=self._zgrab_path,
                sudo=self._config.sudo,
                timeout=self._config.timeout,
            )
        except Exception:
            self._logger.error(
                "Scan ftp error:\ntaskid:{}\batchid:{}\nlevel:{}\nhost:{}\nerror:{}".format(
                    task.taskid,
                    task.batchid,
                    level,
                    portinfo._host,
                    traceback.format_exc(),
                )
            )

    def get_imap_info(
        self, task: IscoutTask, level: int, portinfo: PortInfo, *args
    ) -> iter:
        """get imap info"""
        try:
            self._scanner_imap.get_banner_imap(
                task,
                level,
                portinfo,
                *args,
                zgrab2path=self._zgrab_path,
                sudo=self._config.sudo,
                timeout=self._config.timeout,
            )
        except Exception:
            self._logger.error(
                "Scan imap error:\ntaskid:{}\batchid:{}\nlevel:{}\nhost:{}\nerror:{}".format(
                    task.taskid,
                    task.batchid,
                    level,
                    portinfo._host,
                    traceback.format_exc(),
                )
            )

    def get_pop3_info(
        self, task: IscoutTask, level: int, portinfo: PortInfo, *args
    ) -> iter:
        """get pop3 info"""
        try:
            self._scanner_pop3.get_banner_pop3(
                task,
                level,
                portinfo,
                *args,
                zgrab2path=self._zgrab_path,
                sudo=self._config.sudo,
                timeout=self._config.timeout,
            )
        except Exception:
            self._logger.error(
                "Scan pop3 error:\ntaskid:{}\batchid:{}\nlevel:{}\nhost:{}\nerror:{}".format(
                    task.taskid,
                    task.batchid,
                    level,
                    portinfo._host,
                    traceback.format_exc(),
                )
            )

    def get_mysql_info(
        self, task: IscoutTask, level: int, portinfo: PortInfo, *args
    ) -> iter:
        """get mysql info"""
        try:
            self._scanner_mysql.get_banner_mssql(
                task,
                level,
                portinfo,
                *args,
                zgrab2path=self._zgrab_path,
                sudo=self._config.sudo,
                timeout=self._config.timeout,
            )
        except Exception:
            self._logger.error(
                "Scan mysql error:\ntaskid:{}\batchid:{}\nlevel:{}\nhost:{}\nerror:{}".format(
                    task.taskid,
                    task.batchid,
                    level,
                    portinfo._host,
                    traceback.format_exc(),
                )
            )

    def get_oracle_info(
        self, task: IscoutTask, level: int, portinfo: PortInfo, *args
    ) -> iter:
        """get mysql info"""
        try:
            self._scanner_oracle.get_banner_oracle(
                task,
                level,
                portinfo,
                *args,
                zgrab2path=self._zgrab_path,
                sudo=self._config.sudo,
                timeout=self._config.timeout,
            )
        except Exception:
            self._logger.error(
                "Scan mysql error:\ntaskid:{}\batchid:{}\nlevel:{}\nhost:{}\nerror:{}".format(
                    task.taskid,
                    task.batchid,
                    level,
                    portinfo._host,
                    traceback.format_exc(),
                )
            )
