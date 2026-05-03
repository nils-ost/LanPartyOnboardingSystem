# from .VLAN import TestVLAN, TestVLANApi
# from .Switch import TestSwitch, TestSwitchApi
# from .IpPool import TestIpPool, TestIpPoolApi
# from .Table import TestTable, TestTableApi
# from .Seat import TestSeat, TestSeatApi
# from .Participant import TestParticipant, TestParticipantApi
# from .Device import TestDevice, TestDeviceApi
# from .Session import TestSession, TestSessionApi
from .commitSystem import TestCommitSystem

""" pre commitSystem coverage
------------------------------------------------------------------
HWSwitch/__init__.py                 4      0      0      0   100%
HWSwitch/autoswitch.py              19     12      2      0    33%
HWSwitch/baseswitch.py             268    228    166      0     9%
HWSwitch/dummyswitch.py            196    173     72      0     9%
HWSwitch/helpers.py                 71     63     33      0     8%
HWSwitch/mikrotikswitch.py         330    283    112      0    12%
HWSwitch/parts.py                   76     60     26      0    16%
HWSwitch/testimplementation.py     237    229    102      0     2%
elements/Device.py                 177     95    130     13    43%
elements/IpPool.py                  89     47     53      6    44%
elements/Participant.py             36     13     18      5    59%
elements/Port.py                   252    230    166      0     5%
elements/PortConfigCache.py        148    140     86      0     3%
elements/Seat.py                    59     33     24      4    46%
elements/Session.py                  5      0      0      0   100%
elements/Setting.py                  4      0      0      0   100%
elements/Switch.py                 388    309    205     11    17%
elements/Table.py                   41     10     24      4    75%
elements/VLAN.py                   237    199    102      6    15%
elements/__init__.py                11      0      0      0   100%
endpoints/__init__.py                4      0      0      0   100%
endpoints/metrics.py                81     78     14      0     3%
endpoints/onboarding.py            145    133     74      0     5%
endpoints/participant.py            46     35     16      0    18%
endpoints/switch.py                 85     69     32      0    14%
endpoints/system.py                326    278    132      0    10%
helpers/backgroundworker.py         59     46     20      0    16%
helpers/client.py                   52     45     24      0    14%
helpers/versioning.py              195    187    108      0     3%
main.py                             57      0      0      0   100%
------------------------------------------------------------------
TOTAL                             3698   2995   1741     49    16%
"""
