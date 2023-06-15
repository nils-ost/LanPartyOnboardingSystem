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
    this is done in an order that is unlikely to lock a Switch
    the order is determined by switch_restart_order
    """
    for s in [Switch.get(sid) for sid in switch_restart_order()]:
        s.commit()


def switches_retreat():
    """
    retreats all changes from all Switches
    this is done in an order that is unlikely to lock a Switch
    the order is determined by switch_restart_order
    """
    for s in [Switch.get(sid) for sid in switch_restart_order()]:
        s.retreat()
