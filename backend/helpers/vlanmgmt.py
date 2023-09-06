from elements import VLAN
import subprocess
import os


def vlan_os_interfaces_commit():
    """
    commits all VLANs as os-interfaces
    """
    from helpers.system import check_integrity_vlan_interface_commit
    integrity = check_integrity_vlan_interface_commit()
    if not integrity.get('code', 1) == 0:
        return {'code': 1, 'desc': 'system integrity check failed', 'integrity': integrity}

    fails = list()
    for vlan in VLAN.all():
        if not vlan.commit_os_interface():
            fails.append(vlan['_id'])

    if len(fails) > 0:
        return {'code': 2, 'desc': 'not all VLAN OS-Interfaces could be commited', 'failed': fails}
    else:
        subprocess.call('netplan apply', shell=True)
        return {'code': 0, 'desc': 'done'}


def vlan_os_interfaces_retreat():
    """
    retreats all VLANs os-interfaces
    """
    from helpers.system import check_integrity_vlan_interface_commit
    integrity = check_integrity_vlan_interface_commit()
    if not integrity.get('code', 1) == 0:
        return {'code': 1, 'desc': 'system integrity check failed', 'integrity': integrity}

    fails = list()
    for vlan in VLAN.all():
        if not vlan.retreat_os_interface():
            fails.append(vlan['_id'])

    if len(fails) > 0:
        return {'code': 2, 'desc': 'not all VLAN OS-Interfaces could be retreated', 'failed': fails}
    else:
        subprocess.call('netplan apply', shell=True)
        return {'code': 0, 'desc': 'done'}


def vlan_dnsmasq_config_commit():
    """
    commits all VLANs dnsmasq configs
    """
    from helpers.system import check_integrity_vlan_dnsmasq_commit
    integrity = check_integrity_vlan_dnsmasq_commit()
    if not integrity.get('code', 1) == 0:
        return {'code': 1, 'desc': 'system integrity check failed', 'integrity': integrity}

    fails = list()
    for vlan in VLAN.all():
        if not vlan.commit_dnsmasq_config():
            fails.append(vlan['_id'])

    if len(fails) > 0:
        return {'code': 2, 'desc': 'not all VLAN dnsmasq-configs could be commited', 'failed': fails}
    else:
        try:
            os.remove('/var/lib/misc/dnsmasq.leases')
        except Exception:
            pass
        subprocess.call('systemctl restart dnsmasq', shell=True)
        return {'code': 0, 'desc': 'done'}


def vlan_dnsmasq_config_retreat():
    """
    retreats all VLANs dnsmasq configs
    """
    from helpers.system import check_integrity_vlan_dnsmasq_commit
    integrity = check_integrity_vlan_dnsmasq_commit()
    if not integrity.get('code', 1) == 0:
        return {'code': 1, 'desc': 'system integrity check failed', 'integrity': integrity}

    fails = list()
    for vlan in VLAN.all():
        if not vlan.retreat_dnsmasq_config():
            fails.append(vlan['_id'])

    if len(fails) > 0:
        return {'code': 2, 'desc': 'not all VLAN dnsmasq-configs could be commited', 'failed': fails}
    else:
        try:
            os.remove('/var/lib/misc/dnsmasq.leases')
        except Exception:
            pass
        subprocess.call('systemctl restart dnsmasq', shell=True)
        return {'code': 0, 'desc': 'done'}
