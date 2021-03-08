"""
scanner configs
超时现在都默认设置为30分钟
大规模扫描30分钟的挂起还是能够接受的
modify by judy 2020/08/20
"""
import os
from .scan.plugin.nmap.nmapconfig import NmapConfig
from .scan.plugin.zgrab2.zgrab2config import Zgrab2Config
from .scan.plugin.zmap.zmapconfig import ZmapConfig


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
# 重点区域scantype=2，自定义扫描线程，这个占的资源很重，建议不要多开
# 多线程zmap线程限制，根据内存大小来分配，目前看来2G内存zmap分配3个线程，nmap分配3个线程就已经是极限了
max_zscan_threads = 5
max_nscan_threads = 40  # 这个数字还是根据服务器的性能来改，扫描速度变快，但是结果变少
max_zgrab2_threads = 80  # 这个线程不能多开会耗尽cpu的资源
max_vulns_threads = 160  # 这个线程一般和zgrab2保持一致，可以多开，性能瓶颈在这里

# 性能提升配置
max_zscan_ipranges = 256  # C段IP
max_zscan_ip = 2048  # 单个IP
max_nmap_ip = 256  # nmap ip数

nmap_min_host_group = 1024  # 提升nmap性能，根据性能来，16G千兆带宽使用1024/2048/4096
# 所有扫描的超时时间在config_scanner.py设置，这里只设置nmap的扫描超时，为什么要单独设置呢，因为就这B玩意会爆超时
nmap_tcp_timeout = "10m"  # 设置nmap自身扫描的超时时间，一般大规模扫描15分钟即可
nmap_udp_timeout = "30m"  # 设置nmap的udp扫描超时时间，udp需要的时间比较长，30分钟即可
