import time


def device_scanner():
    from elements import Switch
    time.sleep(3)
    while True:
        new_count = 0
        for switch in Switch.all():
            switch.scan_ports()
            new_count += switch.scan_devices()
        if new_count > 0:
            print(f'Found {new_count} new Devices')
        time.sleep(30)
