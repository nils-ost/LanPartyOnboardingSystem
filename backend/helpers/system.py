from helpers.docdb import docDB
from elements import Setting
from datetime import datetime
import psutil


# time (in seconds) a previous integrity check is considered still as valid
check_max_diff = 30


def get_open_commits():
    result = 0
    for s in docDB.search_many('Switch', {'commited': False}):
        result += 1
    return result


def _check_integrity_switchlinks():
    last_check = Setting.value('integrity_switchlinks')
    if not last_check < 1 and (last_check + check_max_diff) >= datetime.now().timestamp():
        return {'code': 0, 'desc': 'check ok'}
    # Testing, that all Ports marked as switchlink do have a switchlink_port_id filled in,
    # all ports are only used once a switchlink_port_id and corresponding Ports reflect each other
    from elements import Port, Switch
    switchlinks_count = Port.count({'switchlink': True})

    # test if switchlink_count is switches_count * 2 - 2
    if not switchlinks_count == Switch.count() * 2 - 2:
        should = Switch.count() * 2 - 2
        return {'code': 1, 'desc': f'there is a missmatch in how many switchlinks should exist ({should}) and do exist ({switchlinks_count})'}

    none_on = list()
    used = dict()
    not_reflecting = list()
    for p in Port.get_switchlinks():
        # determines None's
        if p['switchlink_port_id'] is None:
            none_on.append(p['_id'])
            continue
        # counting used
        if p['switchlink_port_id'] not in used:
            used[p['switchlink_port_id']] = list()
        used[p['switchlink_port_id']].append(p['_id'])
        # checking reflection
        if not p.switchlink_port()['switchlink_port_id'] == p['_id']:
            not_reflecting.append(p['_id'])

    # error for nones
    if len(none_on) > 0:
        return {'code': 2, 'desc': f'the following switchlinks do not have a switchlink target defined: {none_on}', 'nones': none_on}

    # error for usage
    if not len(used.keys()) == switchlinks_count:
        multiuse = list()
        for sl, p in used.items():
            if len(p) > 1:
                multiuse.append(sl)
        return {'code': 3, 'desc': f'the following ports are used as switchlink targets multiple times: {multiuse}', 'multiuse': multiuse}

    # error for none reflecting
    if len(not_reflecting) > 0:
        return {'code': 4, 'desc': f'the following ports are not reflected by their switchlink targets: {not_reflecting}', 'not_reflecting': not_reflecting}

    Setting.set('integrity_switchlinks', datetime.now().timestamp())
    return {'code': 0, 'desc': 'check ok'}


def _check_integrity_vlans():
    last_check = Setting.value('integrity_vlans')
    if not last_check < 1 and (last_check + check_max_diff) >= datetime.now().timestamp():
        return {'code': 0, 'desc': 'check ok'}
    from elements import VLAN
    # check mgmt VLAN is present
    mgmt_vlan = VLAN.get_by_purpose(1)  # this is a list of VLANs
    if len(mgmt_vlan) == 0:
        return {'code': 5, 'desc': 'mgmt-VLAN is missing'}

    # check play VLAN is present
    play_vlan = VLAN.get_by_purpose(0)  # this is a list of VLANs
    if len(play_vlan) == 0:
        return {'code': 12, 'desc': 'play-VLAN is missing'}

    Setting.set('integrity_vlans', datetime.now().timestamp())
    return {'code': 0, 'desc': 'check ok'}


def _check_integrity_ippools():
    last_check = Setting.value('integrity_ippools')
    if not last_check < 1 and (last_check + check_max_diff) >= datetime.now().timestamp():
        return {'code': 0, 'desc': 'check ok'}
    required_integrity = _check_integrity_vlans()
    if not required_integrity.get('code', 1) == 0:
        return required_integrity

    from elements import VLAN, IpPool
    # check IpPool for mgmt-VLAN is present
    mgmt_vlan = VLAN.get_by_purpose(1)[0]
    mgmt_ippool = IpPool.get_by_vlan(mgmt_vlan['_id'])  # this is a list of IpPools
    if len(mgmt_ippool) == 0:
        return {'code': 6, 'desc': 'IpPool for mgmt-VLAN is missing'}

    # check IpPool for play-VLAN is present
    play_vlan = VLAN.get_by_purpose(0)[0]
    for pool in IpPool.get_by_vlan(play_vlan['_id']):
        if pool['lpos']:
            break
    else:
        return {'code': 13, 'desc': 'no IpPool is defined as LPOS'}

    # check IpPool for all onboarding-VLANs are present
    for ob_vlan in VLAN.get_by_purpose(2):
        ob_pool = IpPool.get_by_vlan(ob_vlan['_id'])
        if not len(ob_pool) == 1:
            return {'code': 14, 'desc': f"IpPool for onboarding VLAN '{ob_vlan['number']}: {ob_vlan['desc']}' is missing"}

    Setting.set('integrity_ippools', datetime.now().timestamp())
    return {'code': 0, 'desc': 'check ok'}


def _check_integrity_tables():
    last_check = Setting.value('integrity_tables')
    if not last_check < 1 and (last_check + check_max_diff) >= datetime.now().timestamp():
        return {'code': 0, 'desc': 'check ok'}
    required_integrity = _check_integrity_ippools()
    if not required_integrity.get('code', 1) == 0:
        return required_integrity

    from elements import Table, Seat, IpPool
    for table in Table.all():
        table_seats = Seat.get_by_table(table['_id'])
        # check if Table has Seats
        nb_seats = len(table_seats)
        if nb_seats == 0:
            return {'code': 15, 'desc': f"no Seats present for Table '{table['number']}: {table['desc']}'"}

        # check if all seats have a number_absolute, if this setting is enabled
        if Setting.value('absolute_seatnumbers'):
            for seat in table_seats:
                if seat['number_absolute'] is None:
                    return {'code': 18, 'desc': f"Seat {seat['number']} of Table '{table['number']}: {table['desc']}' is missing number_absolute"}

        # check if enough IPs for all Seats in play-IpPool of table
        play_pool = table.seat_ip_pool()
        if (play_pool['range_end'] + 1 - play_pool['range_start']) < nb_seats:
            return {'code': 16, 'desc': f"not enough IPs in play-IpPool '{play_pool['desc']}' for Table '{table['number']}: {table['desc']}'"}

        # check if enough IPs in onboarding IpPool (at least half number of seats plus one for LPOS, DNS, DHCP and SSOproxy)
        ob_vlan = table.switch().onboarding_vlan()
        ob_pool = IpPool.get_by_vlan(ob_vlan['_id'])[0]
        if (ob_pool['range_end'] + 1 - ob_pool['range_start']) < (nb_seats / 2 + 5):
            return {'code': 17, 'desc': f"not enough IPs in onboarding-IpPool '{ob_pool['desc']}' for Table '{table['number']}: {table['desc']}'"}

    Setting.set('integrity_tables', datetime.now().timestamp())
    return {'code': 0, 'desc': 'check ok'}


def _check_integrity_lpos():
    last_check = Setting.value('integrity_lpos')
    if not last_check < 1 and (last_check + check_max_diff) >= datetime.now().timestamp():
        return {'code': 0, 'desc': 'check ok'}
    required_integrity = _check_integrity_ippools()
    if not required_integrity.get('code', 1) == 0:
        return required_integrity

    from elements import VLAN, IpPool, Device
    # check LPOS's server network ip for mgmt VLAN is part of the same subnet as mgmt-IpPool
    mgmt_vlan = VLAN.get_by_purpose(1)[0]
    mgmt_ippool = IpPool.get_by_vlan(mgmt_vlan['_id'])[0]
    # determine LPOS's IP
    lpos_ip = None
    for iname, conf in psutil.net_if_addrs().items():
        if iname == 'lo' or 'vlan' in iname:
            continue
        ip, mac = (None, None)
        for e in conf:
            if e.family.name == 'AF_PACKET':
                mac = e.address.replace(':', '')
            if e.family.name == 'AF_INET':
                ip = e.address.split('.')
        if Device.get_by_mac(mac) is not None:
            lpos_ip = IpPool.octetts_to_int(int(ip[0]), int(ip[1]), int(ip[2]), int(ip[3]))
            break
    if lpos_ip is None:
        return {'code': 7, 'desc': 'IP of LPOS server could not be determined'}
    # expand the mask of mgmt_ippool to a usable format
    mask = int('1' * mgmt_ippool['mask'] + '0' * (32 - mgmt_ippool['mask']), 2)
    if not (lpos_ip & mask) == (mgmt_ippool['range_start'] & mask):
        return {'code': 8, 'desc': 'IP of LPOS server is not in the same subnet as mgmt-IpPool'}

    Setting.set('integrity_lpos', datetime.now().timestamp())
    return {'code': 0, 'desc': 'check ok'}


def _check_interity_settings():
    last_check = Setting.value('integrity_settings')
    if last_check is not None and (last_check + check_max_diff) >= datetime.now().timestamp():
        return {'code': 0, 'desc': 'check ok'}

    iname = Setting.value('os_nw_interface')
    if iname == '':
        return {'code': 9, 'desc': "setting 'os_nw_interface' is not defined, but it's needed"}
    # check if it's a valid name and can be found in psutil
    for name in psutil.net_if_addrs().keys():
        if name == iname:
            break
    else:
        return {'code': 10, 'desc': f"invalid hw-interface name '{iname}'"}

    for setting in ['domain', 'subdomain', 'upstream_dns', 'play_gateway', 'play_dhcp']:
        if Setting.value(setting) == '':
            return {'code': 9, 'desc': f"setting '{setting}' is not defined, but it's needed"}

    for setting in ['domain', 'subdomain']:
        s = Setting.value(setting)
        if s.startswith('.') or s.endswith('.'):
            return {'code': 20, 'desc': f"setting '{setting}' is not allowed to start or end with . (dot)"}

    if Setting.value('nlpt_sso'):
        if not Setting.value('absolute_seatnumbers'):
            return {'code': 19, 'desc': 'nlpt_sso is enabled but absolute_seatnumbers is disabled'}
        if Setting.value('sso_login_url') == '':
            return {'code': 9, 'desc': "setting 'sso_login_url' is not defined, but it's needed"}
        if Setting.value('sso_onboarding_url') == '':
            return {'code': 9, 'desc': "setting 'sso_onboarding_url' is not defined, but it's needed"}

    Setting.set('integrity_settings', datetime.now().timestamp())
    return {'code': 0, 'desc': 'check ok'}


def check_integrity():
    """
    do all available integrity checks
    """
    for check in [
            _check_integrity_switchlinks,
            _check_integrity_vlans,
            _check_integrity_ippools,
            _check_integrity_tables,
            _check_integrity_lpos,
            _check_interity_settings]:
        r = check()
        if not r.get('code', 1) == 0:
            return r
    return {'code': 0, 'desc': 'check ok'}


def check_integrity_switch_commit():
    """
    do all integrity checks required for commiting switches
    """
    for check in [_check_integrity_vlans, _check_integrity_ippools, _check_integrity_lpos]:
        r = check()
        if not r.get('code', 1) == 0:
            return r
    return {'code': 0, 'desc': 'check ok'}


def check_integrity_vlan_interface_commit():
    """
    do all integrity checks required for commiting vlan's os_interface
    """
    for check in [_check_interity_settings, _check_integrity_ippools]:
        r = check()
        if not r.get('code', 1) == 0:
            return r
    return {'code': 0, 'desc': 'check ok'}


def check_integrity_vlan_dns_commit():
    """
    do all integrity checks required for commiting vlan's dns server
    """
    for check in [_check_interity_settings, _check_integrity_ippools]:
        r = check()
        if not r.get('code', 1) == 0:
            return r
    return {'code': 0, 'desc': 'check ok'}


def check_integrity_vlan_dhcp_commit():
    """
    do all integrity checks required for commiting vlan's dhcp server
    """
    for check in [_check_interity_settings, _check_integrity_ippools]:
        r = check()
        if not r.get('code', 1) == 0:
            return r
    return {'code': 0, 'desc': 'check ok'}


def check_integrity_haproxy_commit():
    """
    do all integrity checks required for commiting haproxy settings
    """
    for check in [_check_interity_settings]:
        r = check()
        if not r.get('code', 1) == 0:
            return r
    return {'code': 0, 'desc': 'check ok'}


def remove_offline_devices():
    """
    removes all, as offline marked, Devices that do not have a commit-/retreat-config or description

    :returns: count of deleted Devices
    :rtype: int
    """
    from elements import Device
    import time
    deleted_count = 0
    ts = int(time.time()) - 60
    for d in Device.all():
        if d['last_scan_ts'] < ts and d['commit_config'] is None and d['retreat_config'] is None and d['desc'].strip() == '':
            if not d['onboarding_blocked'] and d['seat_id'] is None and d['participant_id'] is None and d['ip_pool_id'] is None and d['ip'] is None:
                d.delete()
                deleted_count += 1
    return deleted_count
