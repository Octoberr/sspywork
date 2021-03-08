"""
scouter插件的一些配置，
因为一些配置是变动的，所以这里做一个配置文件适应变化
"""
# from .scout import PluginConfig
from .scout.pluginconfig import PluginConfig
import os

from .scout.plugin.nmap.nmapconfig import NmapConfig
from .scout.plugin.zgrab2.zgrab2config import Zgrab2Config
from .scout.plugin.zmap.zmapconfig import ZmapConfig

scouter_config = PluginConfig(
    # sonarapi='http://42.99.116.8:9090',  # 部署时使用
    sonarapi="http://192.168.90.14:9090",  # 本地测试用
    iplog_time_limit=3,
)

# sonarapi  sonar的地址，外网应该以sonar的地址为主
# iplog_time_limit  ip历史绑定域名的时间限制，默认取3年内的，不包含3年


nmapconfig = NmapConfig(
    maxthread=5,
    timeout=600,
    sudo=True,
    nmappath=[
        "nmap",
        "/usr/bin/nmap",
        "/usr/local/bin/nmap",
        "/sw/bin/nmap",
        "/opt/local/bin/nmap",
    ],
)

# use "ifconfig" to get the interface card
interface_card: str = "eth0"
zmapconfig = ZmapConfig(
    interface_card=interface_card,
    maxthread=5,
    timeout=600,
    sudo=True,
    zmappath=[
        "zmap",
        "/usr/bin/zmap",
        "/usr/local/bin/zmap",
        "/sw/bin/zmap",
        "/opt/local/bin/zmap",
    ],
)

zgrab2config = Zgrab2Config(
    maxthread=5,
    timeout=600,
    sudo=False,
    zgrab2path=[
        "zgrab2",
        "/usr/bin/zgrab2",
        "/usr/local/bin/zgrab2",
        "/sw/bin/zgrab2",
        "/opt/local/bin/zgrab2",
    ],
)


udp_probes_path: str = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "resource/zmap/udp_probes/",
    )
)
