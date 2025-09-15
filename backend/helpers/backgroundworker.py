import time
import json
from threading import Thread
from queue import Queue


device_scanner_thread = None
device_onboarding_thread = None
device_onboarding_queue = Queue()


def device_scanner():
    from elements import Switch
    time.sleep(3)
    while True:
        new_count = 0
        connected = dict()
        for switch in Switch.all():
            connected[switch['_id']] = switch.connected()
            if connected[switch['_id']]:
                switch.scan_ports()
                switch.scan_devices()
        for switch in Switch.all():
            if connected[switch['_id']]:
                new_count += switch.map_devices()
        if new_count > 0:
            print(f'Found {new_count} new Devices')
        time.sleep(15)


def device_scanner_start():
    global device_scanner_thread
    if device_scanner_thread is None:
        device_scanner_thread = Thread(target=device_scanner, daemon=True)
        device_scanner_thread.start()


def device_onboarding():
    from elements import Device, VLAN, Port
    import logging
    time.sleep(5)
    while True:
        try:
            job = json.loads(device_onboarding_queue.get())
            if 'device' in job:
                device = Device.get(job['device'])
                port_number = device.port()['number']
                # shut off switchport
                device.port().switch().port_disable(port_number)
                # renew vlan config of switchport
                device.port().switch().commit()
                # renew DHCP config of play vlan
                play_vlan = VLAN.get_by_purpose(0)[0]
                play_vlan.commit_dhcp_server()
                # shut on switchport
                device.port().switch().port_enable(port_number)
            elif 'port' in job:
                port = Port.get(job['port'])
                # renew vlan config for switchport
                port.switch().commit()
        except Exception as e:
            logging.error(f'Onboarding error: {e} {repr(e)}')
        finally:
            device_onboarding_queue.task_done()


def device_onboarding_start():
    global device_onboarding_thread
    if device_onboarding_thread is None:
        device_onboarding_thread = Thread(target=device_onboarding, daemon=True)
        device_onboarding_thread.start()


def device_onboarding_schedule(device_id):
    device_onboarding_queue.put(json.dumps({'device': device_id}))


def port_onboarding_schedule(port_id):
    device_onboarding_queue.put(json.dumps({'port': port_id}))
