

def versions_eq(left, right):
    left_l = list()
    for e in left.strip().split('.'):
        try:
            left_l.append(int(e))
        except Exception:
            left_l.append(e)
    right_l = list()
    for e in right.strip().split('.'):
        try:
            right_l.append(int(e))
        except Exception:
            right_l.append(e)
    while len(left_l) < 4:
        left_l.append(0)
    while len(right_l) < 4:
        right_l.append(0)
    for i in range(4):
        if not isinstance(left_l[i], int) == isinstance(right_l[i], int):  # works even if both are str, the result is True
            return False
        if not left_l[i] == right_l[i]:
            return False
    return True


def versions_lt(left, right):
    left_l = list()
    for e in left.strip().split('.'):
        try:
            left_l.append(int(e))
        except Exception:
            left_l.append(e)
    right_l = list()
    for e in right.strip().split('.'):
        try:
            right_l.append(int(e))
        except Exception:
            right_l.append(e)
    while len(left_l) < 4:
        left_l.append(0)
    while len(right_l) < 4:
        right_l.append(0)
    for i in range(4):
        if isinstance(left_l[i], str) and isinstance(right_l[i], int):
            return True
        if isinstance(left_l[i], int) and isinstance(right_l[i], str):
            return False
        if left_l[i] < right_l[i]:
            return True
        if left_l[i] > right_l[i]:
            return False
    return False


def versions_gt(left, right):
    left_l = list()
    for e in left.strip().split('.'):
        try:
            left_l.append(int(e))
        except Exception:
            left_l.append(e)
    right_l = list()
    for e in right.strip().split('.'):
        try:
            right_l.append(int(e))
        except Exception:
            right_l.append(e)
    while len(left_l) < 4:
        left_l.append(0)
    while len(right_l) < 4:
        right_l.append(0)
    for i in range(4):
        if isinstance(left_l[i], str) and isinstance(right_l[i], int):
            return False
        if isinstance(left_l[i], int) and isinstance(right_l[i], str):
            return True
        if left_l[i] > right_l[i]:
            return True
        if left_l[i] < right_l[i]:
            return False
    return False


def versions_lte(left, right):
    if versions_eq(left, right):
        return True
    if versions_lt(left, right):
        return True
    return False


def versions_gte(left, right):
    if versions_eq(left, right):
        return True
    if versions_gt(left, right):
        return True
    return False


def test_compares():
    print('Success' if versions_eq('1.1.1', '1.1.1') is True else 'Fail')
    print('Success' if versions_eq('1.1.1.alpha1', '1.1.1.alpha1') is True else 'Fail')
    print('Success' if versions_eq('1.1.1', '1.1.1.1') is False else 'Fail')
    print('Success' if versions_lt('1.1.1', '1.1.1.1') is True else 'Fail')
    print('Success' if versions_lt('1.1.1.1', '1.1.1') is False else 'Fail')
    print('Success' if versions_lt('1.1.1', '1.1.1') is False else 'Fail')
    print('Success' if versions_gt('1.1.1.1', '1.1.1') is True else 'Fail')
    print('Success' if versions_gt('1.1.1', '1.1.1') is False else 'Fail')
    print('Success' if versions_gt('1.1.1', '1.1.1.1') is False else 'Fail')
    print('Success' if versions_lte('1.1.1', '1.1.1.1') is True else 'Fail')
    print('Success' if versions_lte('1.1.1.1', '1.1.1') is False else 'Fail')
    print('Success' if versions_lte('1.1.1', '1.1.1') is True else 'Fail')
    print('Success' if versions_gte('1.1.1.1', '1.1.1') is True else 'Fail')
    print('Success' if versions_gte('1.1.1', '1.1.1') is True else 'Fail')
    print('Success' if versions_gte('1.1.1', '1.1.1.1') is False else 'Fail')
    print('Success' if versions_lt('1.2.0.alpha1', '1.2.0') is True else 'Fail')
    print('Success' if versions_lt('1.2.0.alpha1', '1.2.0.beta1') is True else 'Fail')
    print('Success' if versions_lt('1.2.0.alpha1', '1.2.0.alpha2') is True else 'Fail')
    print('Success' if versions_lt('1.2.0.beta1', '1.2.0') is True else 'Fail')
    print('Success' if versions_gt('1.2.0', '1.2.0.alpha1') is True else 'Fail')
    print('Success' if versions_gt('1.2.0.beta1', '1.2.0.alpha1') is True else 'Fail')
    print('Success' if versions_gt('1.2.0.alpha2', '1.2.0.alpha1') is True else 'Fail')
    print('Success' if versions_gt('1.2.0', '1.2.0.beta1') is True else 'Fail')


def run():
    import sys
    from helpers.docdb import docDB
    from helpers.version import version as current_version
    from elements import Setting
    db_version = Setting.value('version')
    if db_version is None and docDB.exists('settings', 'version'):
        db_version = docDB.search_one('settings', 'version').get('value', '0.0.0')
    if db_version is None:
        # new install nothing todo
        print('Versioning detected a new install!')
        db_defaults()
        Setting.set('version', current_version)
        return
    if versions_eq(db_version, current_version):
        # nothing todo allready the desired version
        print(f'Versioning detected the DB matches the current version {current_version}')
        return
    if versions_gt(db_version, current_version):
        # error DB is on a newer version that software, better just terminate
        print('Versioning detected the Database is on a newer Version than the software provides! Exiting...')
        sys.exit(0)

    print(f'Versioning performing upgrade from v{db_version} to v{current_version}')

    if versions_lt(db_version, '0.2'):
        print("  Adding 'desc' attribute to Switches")
        for s in docDB.search_many('Switch', {'desc': None}):
            s['desc'] = ''
            docDB.replace('Switch', s)
        print("  Adding 'commit_config' attribute to Ports")
        for p in docDB.search_many('Port', {'commit_config': None}):
            p['commit_config'] = None
            docDB.replace('Port', p)
    if versions_lt(db_version, '0.5.1'):
        from elements import Switch
        print("  Adding 'port_numbering_offset' attribute to Switches")
        for s in docDB.search_many('Switch', {'port_numbering_offset': None}):
            s = Switch(s)
            s['port_numbering_offset'] = 0
            s.save()
    if versions_lt(db_version, '0.6.1'):
        import os
        from elements import Setting
        print('  Migrating settings to Setting-Element')
        for s in docDB.search_many('settings', {}):
            k = s.get('_id')
            v = s.get('value')
            if k is not None and v is not None:
                Setting.set(k, v)
        docDB.clear('settings')
        if os.path.isfile('config.json'):
            import json
            print('  Migrating configs to Setting-Element')
            config = json.load(open('config.json', 'r'))
            if 'port' in config.get('server', dict()):
                Setting.set('server_port', config['server']['port'])
            if 'metrics' in config:
                if 'enabled' in config['metrics']:
                    Setting.set('metrics_enabled', config['metrics']['enabled'])
                if 'port' in config['metrics']:
                    Setting.set('metrics_port', config['metrics']['port'])
            if 'haproxy' in config:
                if 'host' in config['haproxy']:
                    Setting.set('haproxy_api_host', config['haproxy']['host'])
                if 'api_port' in config['haproxy']:
                    Setting.set('haproxy_api_port', config['haproxy']['api_port'])
                if 'api_user' in config['haproxy']:
                    Setting.set('haproxy_api_user', config['haproxy']['api_user'])
                if 'api_pw' in config['haproxy']:
                    Setting.set('haproxy_api_pw', config['haproxy']['api_pw'])
            try:
                os.remove('config.json')
            except Exception:
                pass

    db_defaults()

    Setting.set('version', current_version)


def db_defaults():
    from elements import Participant
    if Participant.count() == 0:
        p = Participant({'login': 'admin', 'pw': 'password', 'admin': True})
        p.save()
        print('Versioning detected no user, therefore created a default admin user')
