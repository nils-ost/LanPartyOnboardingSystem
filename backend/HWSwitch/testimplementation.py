import json
import logging
import copy
from .autoswitch import AutoDetectSwitch

logging.basicConfig(format='%(asctime)s [%(name)-20s] %(levelname)-8s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%z', level='INFO')
logger = logging.getLogger('Testrunner')


# === Call with invoke test-switch


def compare_dumps(a, b=None, cpath=''):
    if not isinstance(a, dict):
        logger.error(f"not a dict '{cpath}'")
        return False

    for k, v in a.items():
        if k not in b:
            logger.error(f"'{k}' not in '{b}'")
            break

        if isinstance(v, dict):
            r = compare_dumps(v, b[k], cpath=f'{cpath}.{k}')
            if not r:
                break

        elif isinstance(v, list):
            if not len(v) == len(b[k]):
                logger.error(f"length missmatch in '{cpath}.{k}'")
                break

            for i in range(len(v)):
                if isinstance(v[i], dict):
                    r = compare_dumps(v[i], b[k][i], cpath=f'{cpath}.{k}.{i}')
                    if not r:
                        break
                else:
                    if 'ports' in cpath and k == 'hosts':
                        continue  # skipping detected hosts, those might change while testing hardware and mess with the result
                    if not v[i] == b[k][i]:
                        logger.error(f"missmatch of '{v[i]}' and '{b[k][i]}' in '{cpath}.{k}.{i}'")
                        break
                    else:
                        logger.debug(f"match in '{cpath}.{k}.{i}'")
            else:
                continue
            break

        elif not v == b[k]:
            logger.error(f"missmatch of '{v}' and '{b[k]}' in '{cpath}.{k}'")
            break

        else:
            logger.debug(f"match in '{cpath}.{k}'")
    else:
        return True
    return False


def run():
    # === getting connection info from user (or save from last run)
    try:
        settings = json.load(open('switch_test_config.json', 'r'))
    except Exception:
        settings = dict()
    host = input(f"Host ({settings.get('host', '')}): ").strip()
    user = input(f"User ({settings.get('user', '')}): ").strip()
    pw = input(f"Password ({settings.get('pw', '')}): ").strip()
    if host == '':
        host = settings.get('host', '')
    if user == '':
        user = settings.get('user', '')
    if pw == '':
        pw = settings.get('pw', '')
    open('switch_test_config.json', 'w').write(json.dumps(dict(host=host, user=user, pw=pw)))

    # === Test1
    logger.info('=== Test1: connection')
    sw = AutoDetectSwitch(host, user, pw)
    if sw.connected:
        logger.info('Test1: pass')
    else:
        logger.critical('Test1: fail')
        return

    # === Test2
    logger.info('=== Test2: switch configuration is ready for test')
    fail = False
    if len(sw.ports) < 8:
        logger.error('at least 8 ports required on switch')
        fail = True
    if len(sw.vlans) > 1:
        logger.error('to many vlans configured on switch')
        fail = True
    if len(sw.vlans) == 1 and not sw.vlans[0].id == 1:
        logger.error('the only vlan allowed to be configured is 1')
        fail = True
    if not sw.vendor == 'nils_ost':  # these tests can be ignored on dummy-switch
        if len(sw.ports[0].hosts) == 0 or not sw.ports[0].link:
            logger.error("you don't seem to be connected to the first port of your switch")
            fail = True
        for idx in range(1, len(sw.ports)):
            if sw.ports[idx].link or len(sw.ports[idx].hosts) > 0:
                logger.error(f"there seems to be something connected to port {idx+1}, don't do this during testing")
                fail = True
    if fail:
        logger.critical('Test2: fail')
        return
    else:
        logger.info('Test2: pass')

    # === Test3
    logger.info('=== Test3: just writing config back should not change anything')
    pre_config = copy.deepcopy(sw.json())
    sw.commitAll()
    sw.reloadAll()
    if compare_dumps(pre_config, sw.json()):
        logger.info('Test3: pass')
        del pre_config
    else:
        logger.critical('Test3: fail')
        return

    # === Test4
    logger.info('=== Test4: adding VLANs')
    sw.vlanAddit(1)
    sw.vlanAddit(2)
    sw.vlanAddit(3)
    sw.vlanAddit(4)
    sw.vlanAddit(5)
    sw.commitNeeded()
    sw2 = AutoDetectSwitch(host, user, pw)
    if compare_dumps(sw.json(), sw2.json()):
        logger.info('Test4: pass')
        del sw2
    else:
        logger.critical('Test4: fail')
        return

    # === Test5
    logger.info('=== Test5: altering VLANs')
    sw.vlanEdit(4, isolation=True, learning=True, mirror=True, igmp=True)
    sw.vlanEdit(5, isolation=False, learning=False, mirror=False, igmp=False)
    sw.commitNeeded()
    sw2 = AutoDetectSwitch(host, user, pw)
    if compare_dumps(sw.json(), sw2.json()):
        logger.info('Test5: pass')
        del sw2
    else:
        logger.critical('Test5: fail')
        return

    # === Test6
    logger.info('=== Test6: removing VLANs')
    sw.vlanRemove(4)
    sw.vlanRemove(5)
    sw.commitNeeded()
    sw2 = AutoDetectSwitch(host, user, pw)
    if compare_dumps(sw.json(), sw2.json()):
        logger.info('Test6: pass')
        del sw2
    else:
        logger.critical('Test6: fail')
        return

    # === Test7
    logger.info('=== Test7: adding members to VLANs')
    for vlan in [2, 3]:
        for port in [1, 2, 3, 4, 5, 6, 7]:
            sw.vlanEdit(vlan, memberAdd=port)
    sw.commitNeeded()
    sw2 = AutoDetectSwitch(host, user, pw)
    if compare_dumps(sw.json(), sw2.json()):
        logger.info('Test7: pass')
        del sw2
    else:
        logger.critical('Test7: fail')
        return

    # === Test8
    logger.info('=== Test8: removing members from VLANs')
    for port in [5, 6, 7]:
        sw.vlanEdit(2, memberRemove=port)
    for port in [1, 2, 3]:
        sw.vlanEdit(3, memberRemove=port)
    sw.commitNeeded()
    sw2 = AutoDetectSwitch(host, user, pw)
    if compare_dumps(sw.json(), sw2.json()):
        logger.info('Test8: pass')
        del sw2
    else:
        logger.critical('Test8: fail')
        return

    # === Test9
    logger.info('=== Test9: disable Port')
    sw.portEdit(2, enabled=False)
    sw.commitNeeded()
    sw2 = AutoDetectSwitch(host, user, pw)
    if compare_dumps(sw.json(), sw2.json()):
        logger.info('Test9: pass')
        del sw2
    else:
        logger.critical('Test9: fail')
        return

    # === Test10
    logger.info('=== Test10: enable Port')
    sw.portEdit(2, enabled=True)
    sw.commitNeeded()
    sw2 = AutoDetectSwitch(host, user, pw)
    if compare_dumps(sw.json(), sw2.json()):
        logger.info('Test10: pass')
        del sw2
    else:
        logger.critical('Test10: fail')
        return

    # === Test11
    logger.info('=== Test11: disable Port forwarding')
    for p in range(2, len(sw.ports)):
        sw.portEdit(1, fwdNotTo=p)
    sw.commitNeeded()
    sw2 = AutoDetectSwitch(host, user, pw)
    if compare_dumps(sw.json(), sw2.json()):
        logger.info('Test11: pass')
        del sw2
    else:
        logger.critical('Test11: fail')
        return

    # === Test12
    logger.info('=== Test12: enable Port forwarding')
    for p in range(2, len(sw.ports)):
        sw.portEdit(1, fwdTo=p)
    sw.commitNeeded()
    sw2 = AutoDetectSwitch(host, user, pw)
    if compare_dumps(sw.json(), sw2.json()):
        logger.info('Test12: pass')
        del sw2
    else:
        logger.critical('Test12: fail')
        return

    # === Test13
    logger.info('=== Test13: alter Ports VLAN config')
    sw.portEdit(0, vmode='optional', vreceive='any', vdefault=1, vforce=False)  # mandatory for Test14
    sw.portEdit(1, vmode='disabled', vreceive='any', vdefault=1, vforce=False)
    sw.portEdit(2, vmode='optional', vreceive='only tagged', vdefault=1, vforce=False)
    sw.portEdit(3, vmode='enabled', vreceive='only untagged', vdefault=2, vforce=False)
    sw.portEdit(4, vmode='strict', vreceive='any', vdefault=2, vforce=False)
    sw.portEdit(5, vmode='optional', vreceive='only untagged', vdefault=3, vforce=True)
    sw.portEdit(6, vmode='enabled', vreceive='only tagged', vdefault=3, vforce=True)
    sw.portEdit(7, vmode='strict', vreceive='only untagged', vdefault=3, vforce=False)
    sw.commitNeeded()
    sw2 = AutoDetectSwitch(host, user, pw)
    if compare_dumps(sw.json(), sw2.json()):
        logger.info('Test13: pass')
        del sw2
    else:
        logger.critical('Test13: fail')
        return

    # === Test14
    logger.info('=== Test14: change mgmt vlan')
    sw.setMgmtVlan(1)
    sw.commitNeeded()
    sw2 = AutoDetectSwitch(host, user, pw)
    if compare_dumps(sw.json(), sw2.json()):
        logger.info('Test14: pass')
        del sw2
    else:
        logger.critical('Test14: fail')
        return

    # === Test15
    logger.info('=== Test15: reset Switch config')
    sw.setMgmtVlan()  # reset to none
    sw.vlanAddit(1)
    sw.commitNeeded()
    for p in sw.ports:
        sw.portEdit(p, enabled=True, vmode='optional', vreceive='any', vdefault=1, vforce=False)
        for idx in range(len(sw.ports)):
            if not p.idx == idx:
                sw.portEdit(p, fwdTo=idx)
    for idx in range(len(sw.ports)):
        sw.vlanEdit(1, memberAdd=idx)
    vids = list()
    for v in sw.vlans:  # don't alter over a changeing list
        if not v.id == 1:
            vids.append(v.id)
    for vid in vids:
        sw.vlanRemove(vid)
    sw.commitNeeded()
    sw2 = AutoDetectSwitch(host, user, pw)
    if compare_dumps(sw.json(), sw2.json()):
        logger.info('Test15: pass')
        del sw2
    else:
        logger.critical('Test15: fail')
        return
