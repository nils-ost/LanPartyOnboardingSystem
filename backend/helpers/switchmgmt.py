from elements import Switch, Port


def _chain_len(d):
    result = 0
    for v in d.values():
        result += 1
        result += _chain_len(v)
    return result


def switch_hierarchy():
    def next_hop(current, parent=None):
        result = dict()
        for sl in Port.get_switchlinks(current['_id']):
            sl_result = dict()
            if parent is None or parent.mac_addr() not in sl.scanned_hosts():
                for slh in sl.scanned_hosts():
                    for s in Switch.all():
                        if s.mac_addr() == slh:
                            sl_result[s['_id']] = next_hop(s, current)
            max_id, max_len = (None, None)
            for s_id, hops_len in [(s_id, _chain_len(hops)) for s_id, hops in sl_result.items()]:
                if max_len is None or hops_len > max_len:
                    max_id = s_id
                    max_len = hops_len
            if max_id is not None:
                result[max_id] = sl_result[max_id]
        return result

    lpos = Port.get_lpos()
    result = dict()
    result[lpos.switch()['_id']] = next_hop(lpos.switch(), None)
    return result


def switch_restart_order():
    def determine_restart(d, restart_order):
        for k, v in d.items():
            if _chain_len(v) > 0:
                determine_restart(v, restart_order)
            restart_order.append(k)

    result = list()
    determine_restart(switch_hierarchy(), result)
    return result


def switches_commit():
    """
    commits all changes to all Switches
    this is done in an order that is unlikely to lock a Switch.
    The order is determined by switch_restart_order
    """
    restart_order = switch_restart_order()
    if len(restart_order) < len(Switch.all()):
        missing = list([s['_id'] for s in Switch.all() if s['_id'] not in restart_order])
        return {'code': 1, 'desc': 'missing Switches in restart order', 'missing': missing}
    elif len(restart_order) > len(Switch.all()):
        return {'code': 2, 'desc': 'to many Switches in restart order'}

    retry = list()
    for s in [Switch.get(sid) for sid in restart_order]:
        try:
            s.commit()
        except Exception:
            retry.append(s)

    failed = list()
    for s in retry:
        try:
            s.commit()
        except Exception:
            failed.append(s['_id'])

    if len(failed) > 0:
        return {'code': 3, 'desc': 'not all Switches could be commited', 'failed': failed}
    else:
        return {'code': 0, 'desc': 'done'}


def switches_retreat():
    """
    retreats all changes from all Switches
    this is done in an order that is unlikely to lock a Switch.
    The order is determined by switch_restart_order
    """
    restart_order = switch_restart_order()
    if len(restart_order) < len(Switch.all()):
        missing = list([s['_id'] for s in Switch.all() if s['_id'] not in restart_order])
        return {'code': 1, 'desc': 'missing Switches in restart order', 'missing': missing}
    elif len(restart_order) > len(Switch.all()):
        return {'code': 2, 'desc': 'to many Switches in restart order'}

    retry = list()
    for s in [Switch.get(sid) for sid in restart_order]:
        try:
            s.retreat()
        except Exception:
            retry.append(s)

    failed = list()
    for s in retry:
        try:
            s.retreat()
        except Exception:
            failed.append(s['_id'])

    if len(failed) > 0:
        return {'code': 3, 'desc': 'not all Switches could be retreated', 'failed': failed}
    else:
        return {'code': 0, 'desc': 'done'}
