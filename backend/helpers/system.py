from helpers.docdb import docDB


def get_commited():
    result = docDB.get_setting('system_commited')
    if result is None:
        return False
    else:
        return result


def set_commited(state):
    docDB.set_setting('system_commited', state)


def get_open_commits():
    result = 0
    for s in docDB.search_many('Switch', {'commited': False}):
        result += 1
    return result


def check_integrity():
    # Testing, that all Ports marked as switchlink do have a switchlink_port_id filled in,
    # all ports are only used once a switchlink_port_id and corresponding Ports reflect each other
    import psutil
    from elements import Port, Switch, VLAN, IpPool, Device
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

    # check mgmt VLAN is present
    mgmt_vlan = VLAN.get_by_purpose(1)  # this is currently a list of VLANs
    if len(mgmt_vlan) == 0:
        return {'code': 5, 'desc': 'mgmt-VLAN is missing'}
    mgmt_vlan = mgmt_vlan[0]  # "unlist" the variable

    # check IpPool for mgmt-VLAN is present
    mgmt_ippool = IpPool.get_by_vlan(mgmt_vlan['_id'])  # this is currently a list of IpPools
    if len(mgmt_ippool) == 0:
        return {'code': 6, 'desc': 'IpPool for mgmt-VLAN is missing'}
    mgmt_ippool = mgmt_ippool[0]  # "unlist" the variable

    # check LPOS's server network ip for mgmt VLAN is part of the same subnet as mgmt-IpPool
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

    # TODO:
    # prüfen ob setting os_nw_interface gesetzt ist und das entsprechende interface in psutil gefunden werden kann
    # pruefen, dass groeße der IP-Pools zu vohanden Sitzen am tisch passt
    # pruefen, dass fuer jeden tisch ein play IpPool vorhanden - obsolet, macht Table element selbst
    # pruefen, dass ein additional play IpPool vorhanden - obsolet, macht Table element selbst
    # pruefen, dass fuer jedes OnBoarding VLAN ein IpPool vorhanden, und dieser zur groeße des tisches passt (+ 1 für LPOS)

    # returning code, that is signaling the whole check is completed and resultet in no errors
    return {'code': 0, 'desc': 'check ok'}
