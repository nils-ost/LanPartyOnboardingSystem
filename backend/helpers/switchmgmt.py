from elements import Switch, Port


def _chain_len(d):
    result = 0
    for v in d.values():
        result += 1
        result += _chain_len(v)
    return result


def switch_hierarchy(start_switch=None):
    """
    builds a dict thats represents the hierachy of Switches conneceted to eachother,
    starting with the Switch that is hosting the lpos server.
    this is done by iterating over all switchlink_port_ids of every switchlink-Port contained on a Switch

    if start_switch is set (as Switch or SwitchID) only the subtree starting at this Switch is returend
    """
    scanned_switches = list()

    def next_hop(current_sw):
        scanned_switches.append(current_sw['_id'])
        result = dict()
        for sl in Port.get_switchlinks(current_sw['_id']):
            if sl.switchlink_port() is None:
                continue
            sl_switch = sl.switchlink_port().switch()
            if sl_switch['_id'] in scanned_switches:
                continue
            result[sl_switch['_id']] = next_hop(sl_switch)
        return result

    def find_subtree(tree, start_switch):
        for switch, subtree in tree.items():
            if switch == start_switch:
                return {switch: subtree}
            result = find_subtree(subtree, start_switch)
            if result is not None:
                return result
        return None

    lpos = Port.get_lpos()
    result = dict()
    if lpos is None:
        return result
    result[lpos.switch()['_id']] = next_hop(lpos.switch())
    if start_switch is not None and (isinstance(start_switch, Switch) or isinstance(start_switch, str)):
        if isinstance(start_switch, Switch):
            start_switch = start_switch['_id']
        return find_subtree(result, start_switch)
    return result


def switch_restart_order(start_switch=None):
    """
    builds a list of SwitchIDs representing the preferred order of Switches to be restarted
    this is done by taking the switch_hierarchy into count, from where the most outer leaves are the first Switches to be restarted

    if start_switch is set (as Switch or SwitchID) only the corresponding subtree of switch_hierarchy is returned
    """
    def determine_restart(d, restart_order):
        for k, v in d.items():
            if _chain_len(v) > 0:
                determine_restart(v, restart_order)
            restart_order.append(k)

    result = list()
    determine_restart(switch_hierarchy(start_switch), result)
    return result


def switches_commit():
    """
    commits all changes to all Switches
    this is done in an order that is unlikely to lock a Switch.
    The order is determined by switch_restart_order
    """
    from helpers.system import check_integrity
    integrity = check_integrity()
    if not integrity.get('code', 1) == 0:
        return {'code': 1, 'desc': 'system integrity check failed', 'integrity': integrity}

    restart_order = switch_restart_order()
    if len(restart_order) < Switch.count():
        missing = list([s['_id'] for s in Switch.all() if s['_id'] not in restart_order])
        return {'code': 2, 'desc': 'missing Switches in restart order', 'missing': missing}
    elif len(restart_order) > Switch.count():
        return {'code': 3, 'desc': 'to many Switches in restart order'}

    # stages are executed in the order of appearence
    stages = ['vlans', 'vlan_memberships', 'isolation', 'port_vlans']
    switches = list([Switch.get(sid) for sid in restart_order])
    fails = list()

    for stage in stages:
        retry = False
        to_retry = list()
        stage_fail = list()
        switches_to_exec = switches
        while True:
            for s in switches_to_exec:
                fail = False
                executor = None
                if stage == 'vlans':
                    executor = s._commit_vlans
                elif stage == 'vlan_memberships':
                    executor = s._commit_vlan_memberships
                elif stage == 'isolation':
                    executor = s._commit_isolation
                elif stage == 'port_vlans':
                    executor = s._commit_port_vlans

                try:
                    if not executor():
                        fail = True
                except Exception:
                    fail = True

                if fail:
                    if retry:
                        stage_fail.append(s)
                    else:
                        to_retry.append(s)

            if retry or len(to_retry) == 0:
                break
            switches_to_exec = to_retry
            retry = True

        for s in stage_fail:
            fails.append((s['_id'], stage))
            switches.remove(s)

    if len(fails) > 0:
        return {'code': 4, 'desc': 'not all Switches could be commited', 'failed': fails}
    else:
        return {'code': 0, 'desc': 'done'}


def switches_retreat():
    """
    retreats all changes from all Switches
    this is done in an order that is unlikely to lock a Switch.
    The order is determined by switch_restart_order
    """
    from helpers.system import check_integrity
    integrity = check_integrity()
    if not integrity.get('code', 1) == 0:
        return {'code': 1, 'desc': 'system integrity check failed', 'integrity': integrity}

    restart_order = switch_restart_order()
    if len(restart_order) < Switch.count():
        missing = list([s['_id'] for s in Switch.all() if s['_id'] not in restart_order])
        return {'code': 2, 'desc': 'missing Switches in restart order', 'missing': missing}
    elif len(restart_order) > Switch.count():
        return {'code': 3, 'desc': 'to many Switches in restart order'}

    # stages are executed in the order of appearence
    stages = ['port_vlans', 'isolation', 'vlan_memberships', 'vlans']
    switches = list([Switch.get(sid) for sid in restart_order])
    fails = list()

    for stage in stages:
        retry = False
        to_retry = list()
        stage_fail = list()
        switches_to_exec = switches
        while True:
            for s in switches_to_exec:
                fail = False
                executor = None
                if stage == 'vlans':
                    executor = s._retreat_vlans
                elif stage == 'vlan_memberships':
                    executor = s._retreat_vlan_memberships
                elif stage == 'isolation':
                    executor = s._retreat_isolation
                elif stage == 'port_vlans':
                    executor = s._retreat_port_vlans

                try:
                    if not executor():
                        fail = True
                except Exception:
                    fail = True

                if fail:
                    if retry:
                        stage_fail.append(s)
                    else:
                        to_retry.append(s)

            if retry or len(to_retry) == 0:
                break
            switches_to_exec = to_retry
            retry = True

        for s in stage_fail:
            fails.append((s['_id'], stage))
            switches.remove(s)

    if len(fails) > 0:
        return {'code': 4, 'desc': 'not all Switches could be retreated', 'failed': fails}
    else:
        return {'code': 0, 'desc': 'done'}
