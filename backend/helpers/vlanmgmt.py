from elements import VLAN


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
        return {'code': 0, 'desc': 'done'}


def vlan_dns_server_commit():
    """
    commits all VLANs DNS-Servers
    """
    from helpers.system import check_integrity_vlan_dns_commit
    integrity = check_integrity_vlan_dns_commit()
    if not integrity.get('code', 1) == 0:
        return {'code': 1, 'desc': 'system integrity check failed', 'integrity': integrity}

    fails = list()
    for vlan in VLAN.all():
        if not vlan.commit_dns_server():
            fails.append(vlan['_id'])

    if len(fails) > 0:
        return {'code': 2, 'desc': 'not all VLAN DNS-Servers could be commited', 'failed': fails}
    return {'code': 0, 'desc': 'done'}


def vlan_dns_server_retreat():
    """
    retreats all VLANs DNS-Servers
    """
    fails = list()
    for vlan in VLAN.all():
        if not vlan.retreat_dns_server():
            fails.append(vlan['_id'])

    if len(fails) > 0:
        return {'code': 2, 'desc': 'not all VLAN DNS-Servers could be retreated', 'failed': fails}
    return {'code': 0, 'desc': 'done'}


def vlan_dhcp_server_commit():
    """
    commits all VLANs DHCP-Servers
    """
    from helpers.system import check_integrity_vlan_dhcp_commit
    integrity = check_integrity_vlan_dhcp_commit()
    if not integrity.get('code', 1) == 0:
        return {'code': 1, 'desc': 'system integrity check failed', 'integrity': integrity}

    fails = list()
    for vlan in VLAN.all():
        if not vlan.commit_dhcp_server():
            fails.append(vlan['_id'])

    if len(fails) > 0:
        return {'code': 2, 'desc': 'not all VLAN DHCP-Servers could be commited', 'failed': fails}
    return {'code': 0, 'desc': 'done'}


def vlan_dhcp_server_retreat():
    """
    retreats all VLANs DHCP-Servers
    """
    fails = list()
    for vlan in VLAN.all():
        if not vlan.retreat_dhcp_server():
            fails.append(vlan['_id'])

    if len(fails) > 0:
        return {'code': 2, 'desc': 'not all VLAN DHCP-Servers could be retreated', 'failed': fails}
    return {'code': 0, 'desc': 'done'}
