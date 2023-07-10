from helpers.docdb import docDB


def get_commited():
    result = docDB.get('system', 'commited')
    if result is None:
        return False
    else:
        return result.get('state', False)


def set_commited(state):
    if not docDB.update('system', 'commited', {'state': state}):
        docDB.create('system', 'commited', {'state': state})


def get_open_commits():
    result = 0
    for s in docDB.search_many('Switch', {'commited': False}):
        result += 1
    return result


def check_integrity():
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
    if not len(used.key()) == switchlinks_count:
        multiuse = list()
        for sl, p in used.items():
            if len(p) > 1:
                multiuse.append(sl)
        return {'code': 3, 'desc': f'the following ports are used as switchlink targets multiple times: {multiuse}', 'multiuse': multiuse}

    # error for none reflecting
    if len(not_reflecting) > 0:
        return {'code': 4, 'desc': f'the following ports are not reflected by their switchlink targets: {not_reflecting}', 'not_reflecting': not_reflecting}

    # returning code, that is signaling the whole check is completed and resultet in no errors
    return {'code': 0, 'desc': 'check ok'}
