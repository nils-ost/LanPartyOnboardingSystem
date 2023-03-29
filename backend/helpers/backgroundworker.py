import time


def device_scanner():
    from elements import Switch
    while True:
        time.sleep(30)
        new_count = 0
        for switch in Switch.all():
            new_count += switch.scan_devices()
        if new_count > 0:
            print(f'Found {new_count} new Devices')
