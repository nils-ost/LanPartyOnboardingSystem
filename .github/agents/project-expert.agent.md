# LPOS — Project Expert Agent Reference (Deep Knowledge)

## Table of Contents
- [Element/Model Classes](#elementmodel-classes)
- [Endpoint/API Routes](#endpointapi-routes)
- [Helper/Utility Files](#helperutility-files)
- [Frontend Components](#frontend-components)
- [Frontend Services](#frontend-services)
- [TypeScript Interfaces](#typescript-interfaces)
- [Startup/Boot Sequence](#startupboot-sequence)
- [Key File Paths Reference](#key-file-paths-reference)

---

## Element/Model Classes

### VLAN (`backend/elements/VLAN.py`)

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `number` | int | unique, notnone | VLAN ID (1-1024) |
| `purpose` | int | default=3, notnone | 0=play, 1=mgmt, 2=onboarding, 3=other |
| `desc` | str | default='' | Description |

| Method | Return | Description |
|--------|--------|-------------|
| `get_by_number(number)` | VLAN\|None | Find by VLAN number |
| `get_by_purpose(purpose)` | list[VLAN] | Find all with given purpose |
| `validate()` | dict errors | Validates number range, uniqueness for purposes 0/1 |
| `save_post()` | void | Clears PortConfigCache for all ports |
| `delete_pre()` | dict\|None | Prevents deletion if IpPool or Switch references exist; removes VLAN from all switches/ports |
| `delete_post()` | void | Clears PortConfigCache for all ports |
| `commit_os_interface()` | bool | Creates Docker ipvlan network, attaches HAProxy containers |
| `retreat_os_interface()` | bool | Disconnects and removes Docker ipvlan network |
| `commit_dns_server()` | bool | Starts CoreDNS container with hosts file mapping |
| `retreat_dns_server()` | bool | Stops CoreDNS container and removes volume |
| `commit_dhcp_server()` | bool | Starts Kea-DHCP4 container with reservation-based config |
| `retreat_dhcp_server()` | bool | Stops Kea-DHCP4 container |

**Validation Error Codes**: 10 (number range), 11 (purpose range), 12 (duplicate purpose 0/1)

---

### Switch (`backend/elements/Switch.py`)

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `desc` | str | default='' | Description |
| `addr` | str | unique, notnone | IP/hostname of switch |
| `user` | str | default='' | SSH username |
| `pw` | str | default='' | SSH password |
| `purpose` | int | default=0 | 0=core, 1=participants, 2=mixed |
| `commited` | bool | default=False | Whether config is applied to hardware |
| `onboarding_vlan_id` | str\|None | FK→VLAN | Onboarding VLAN (required for purpose 1/2) |
| `port_numbering_offset` | int | default=0 | Offset for port display numbers |

| Method | Return | Description |
|--------|--------|-------------|
| `validate()` | dict errors | Validates purpose, onboarding_vlan_id references and uniqueness |
| `save_pre()` | void | Clears onboarding_vlan_id if purpose==0; sets offset default |
| `save_post()` | void | Updates switch_objects cache, scans VLANs/ports, updates Port display numbers |
| `delete_pre()` | dict\|None | Prevents deletion if Table references exist |
| `delete_post()` | void | Deletes all associated Ports |
| `connected()` | bool | Checks SSH connection via AutoDetectSwitch cache |
| `mac_addr()` | str | Returns switch MAC address |
| `scan_devices()` | bool | Reloads ports and hosts from switch |
| `map_devices()` | int | Maps detected devices to Port/Device records; returns new device count |
| `scanned_port_hosts(port_idx)` | list[str] | MAC addresses on a specific port |
| `scan_vlans()` | int | Scans VLANs from switch; creates unknown ones as purpose=3 |
| `scan_ports()` | int | Scans ports from switch; creates unknown ones in DB |
| `known_vlans()` | list[str] | List of VLAN IDs known on this switch |
| `add_vlan(vlan_id)` | int | Adds VLAN to switch (0=success, 1=not connected, 2=vlan not found) |
| `remove_vlan(vlan_id)` | int | Removes VLAN from switch |
| `port_disable(port_number)` | int | Disables a port on the switch |
| `port_enable(port_number)` | int | Enables a port on the switch |
| `_retreat_vlans()` | bool | Removes LPOS-managed VLANs from hardware config |
| `_retreat_vlan_memberships()` | void | Removes VLAN memberships from ports |
| `_commit_vlans()` | bool | Adds required VLANs to switch |
| `_commit_vlan_memberships()` | bool | Assigns ports to correct VLANs |
| `_commit_isolation()` | bool | Configures port isolation |
| `_commit_port_vlans()` | bool | Sets per-port VLAN configurations |

**Global State**: `switch_objects = dict()`, `switch_macs = list()` — module-level caches

---

### Device (`backend/elements/Device.py`)

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `mac` | str | unique, notnone | MAC address (normalized, no colons) |
| `desc` | str | default='' | Description (auto-set from Participant name) |
| `seat_id` | str\|None | FK→Seat | Seat this device is assigned to |
| `participant_id` | str\|None | FK→Participant | Participant who owns this device |
| `ip_pool_id` | str\|None | FK→IpPool | IP pool for address assignment |
| `ip` | int\|None | unique | IP as integer (auto-calculated) |
| `port_id` | str\|None | FK→Port | Port this device is connected to |
| `onboarding_blocked` | bool | default=False | Blocked after 3 wrong password attempts |
| `pw_strikes` | int | default=0 | Failed password attempt counter |
| `last_scan_ts` | int | default=0 | Last scan timestamp |
| `commit_config` | dict\|None | Manual commit config | Port/device VLAN configuration for commit scope |
| `retreat_config` | dict\|None | Manual retreat config | Port/device VLAN configuration for retreat scope |

**commit_config/retreat_config structure**:
```python
{
    'enabled': bool,      # True/False
    'force': bool,        # Force mode
    'mode': str,          # 'disabled'|'optional'|'enabled'|'strict'
    'receive': str,       # 'any'|'only tagged'|'only untagged'
    'vlans': [str],       # List of VLAN IDs (at least one)
    'default': str        # Default VLAN ID (first in list if not set)
}
```

| Method | Return | Description |
|--------|--------|-------------|
| `get_by_mac(mac)` | Device\|None | Find by MAC address |
| `get_by_port(port_id)` | list[Device] | Find all devices on a port |
| `get_by_seat(seat_id)` | Device\|None | Find device assigned to seat |
| `get_by_ip(ip)` | Device\|None | Find by IP integer |
| `validate()` | dict errors | Complex validation: FK checks, auto-sets participant from seat, auto-calculates IP from pool |
| `save_pre()` | void | Sets desc from Participant name; caches port_id for change detection |
| `save_post()` | void | Invalidates PortConfigCache for old and new ports |
| `delete_post()` | void | Invalidates PortConfigCache |

**Validation Error Codes**: 60 (FK not found), 61 (wrong VLAN purpose for participant), 62 (pool conflict with Table), 63/64 (IP range), 65 (invalid config mode/receive value), 66 (missing vlans in config)

---

### Seat (`backend/elements/Seat.py`)

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `number` | int | default=1, notnone | Seat number within table (1-based) |
| `number_absolute` | int\|None | unique | Absolute seat number across all tables |
| `pw` | str\|None | default=None | Password for claiming this seat |
| `table_id` | str | notnone, FK→Table | Parent table |
| `claiming_device_id` | str\|None | FK→Device | Device currently claiming this seat |

| Method | Return | Description |
|--------|--------|-------------|
| `get_by_table(table_id)` | list[Seat] | All seats in a table |
| `get_by_number(table_id, number)` | Seat\|None | Seat by local number within table |
| `get_by_number_absolute(number)` | Seat\|None | Seat by absolute number |
| `get_by_claiming(device_id)` | Seat\|None | Seat being claimed by a device |
| `validate()` | dict errors | Validates table exists, number uniqueness per table, range bounds |
| `delete_post()` | void | Clears seat/device associations for all related devices and participants |

**Validation Error Codes**: 50 (table not found), 51/52 (number range/uniqueness), 53 (negative absolute), 54 (exceeds IP pool range)

---

### Table (`backend/elements/Table.py`)

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `number` | int | unique, notnone | Table number |
| `desc` | str | default='' | Description |
| `switch_id` | str | notnone, FK→Switch | Switch this table is on (must be purpose 1 or 2) |
| `seat_ip_pool_id` | str | unique, notnone, FK→IpPool | IP pool for seat devices (play VLAN only) |
| `add_ip_pool_id` | str | notnone, FK→IpPool | Additional IP pool for extra devices |

| Method | Return | Description |
|--------|--------|-------------|
| `get_by_number(number)` | Table\|None | Find by table number |
| `validate()` | dict errors | Validates switch purpose, pool VLAN purposes, mutual exclusivity of pools |
| `delete_pre()` | dict\|None | Prevents deletion if Seats exist |

**Validation Error Codes**: 40 (number range), 41 (FK not found), 42/43 (wrong VLAN purpose), 44/46 (pool already used by other table), 45 (same pool for both)

---

### Participant (`backend/elements/Participant.py`)

Extends `UserBase` from noAPIframe.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `login` | str\|None | From UserBase | Login identifier |
| `pw` | str\|None | From UserBase | Password hash |
| `admin` | bool | From UserBase | Admin flag |
| `name` | str | default='', notnone | Display name |
| `seat_id` | str\|None | unique, FK→Seat | Primary seat assignment |

| Method | Return | Description |
|--------|--------|-------------|
| `validate()` | dict errors | Validates seat exists if set |
| `get_by_seat(seat_id)` | Participant\|None | Find by seat |
| `delete_pre()` | void | Calls `offboard()` to clean up devices |
| `delete_post()` | void | Deletes all associated Sessions |
| `offboard()` | void | Deletes all related Devices, clears seat_id |

**Validation Error Codes**: 70 (seat not found)

---

### Port (`backend/elements/Port.py`)

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `number` | int | notnone | Physical port number on switch |
| `number_display` | int | default=None | Display number (number + offset) |
| `desc` | str | default='' | Description |
| `switch_id` | str | notnone, FK→Switch | Parent switch |
| `participants` | bool | default=False | Whether port is for participant devices |
| `switchlink` | bool | default=False | Whether this is a switch-to-switch link |
| `switchlink_port_id` | str\|None | FK→Port | Paired switchlink port (bidirectional) |
| `commit_disabled` | bool | default=False | Skip commit config for this port |
| `retreat_disabled` | bool | default=False | Skip retreat config for this port |
| `commit_config` | dict\|None | Manual commit config | Same structure as Device.commit_config |
| `retreat_config` | dict\|None | Manual retreat config | Same structure as Device.retreat_config |

**Read-only attributes** (set by endpoint, not stored in DB): `switchlink`, `number_display`

| Method | Return | Description |
|--------|--------|-------------|
| `get_by_number(switch_id, number)` | Port\|None | Find port on a switch |
| `get_lpos()` | Port\|None | Returns the port LPOS server is connected to |
| `get_switchlinks(switch_id=None)` | list[Port] | All switchlink ports (optionally filtered by switch) |
| `validate()` | dict errors | Validates FKs, number uniqueness, switchlink reflection, config structure |
| `save_pre()` | void | Sets display number; enforces switchlink/participants rules based on switch purpose |
| `save_post()` | void | Syncs switchlink_port_id bidirectionally; invalidates PortConfigCache |
| `delete_post()` | void | Clears paired switchlink_port_id; invalidates PortConfigCache |
| `vlan_ids()` | list[str] | VLAN IDs currently active on this port (from live switch) |
| `default_vlan_id()` | str\|None | Default VLAN ID from live switch |
| `type()` | str | Port type from live switch (e.g., '10/100/1000') |
| `enabled()` | bool | Whether port is enabled on live switch |
| `link()` | bool | Whether link is up on live switch |
| `speed()` | str | Link speed from live switch |
| `receive()` | str | VLAN receive mode from live switch |
| `scanned_hosts()` | list[str] | MAC addresses detected on this port |

**Validation Error Codes**: 90 (FK not found), 91/92 (number range/uniqueness), 93 (switchlink target not a switchlink), 94 (invalid config mode/receive), 95 (missing vlans)

---

### PortConfigCache (`backend/elements/PortConfigCache.py`)

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `port_id` | str | notnone, FK→Port | Parent port |
| `scope` | int | notnone | 0=commit scope, 1=retreat scope |
| `device_desc` | str | default='' | Description of device config source |
| `isolate` | bool | default=False | Whether port should be isolated |
| `vlan_ids` | list[str] | default=[] | VLANs to apply |
| `default_vlan_id` | str\|None | FK→VLAN | Default PVID |
| `enabled` | bool | default=True | Port enabled state |
| `mode` | str | default='optional' | VLAN mode: 'strict'\|'optional' |
| `receive` | str | default='any' | Receive mode: 'any'\|'only tagged'\|'only untagged' |
| `force` | bool | default=False | Force mode flag |

**Read-only**: All attributes (endpoint sets `_ro_all = True`)

| Method | Return | Description |
|--------|--------|-------------|
| `get_by_port(port_id, scope=0)` | PortConfigCache | Gets or auto-generates cache entry |
| `delete_by_port(port_id)` | void | Deletes all cache entries for a port |
| `_generate()` | void | Auto-generates config based on scope, port type, device configs |

**Generation Logic (scope=0 commit)**:
1. LPOS port → mgmt VLAN + play VLAN + all onboarding VLANs, receive='any'
2. Switchlink port → mgmt + play + onboarding VLANs + other_vlans, receive='only tagged'
3. Device with commit_config → use device config (if single device)
4. Port with manual commit_config → use port config
5. Core switch (no onboarding VLAN) → play VLAN only
6. Non-participant port → play VLAN only
7. Participant port with configured device → play VLAN; else → onboarding VLAN + isolate

---

### IpPool (`backend/elements/IpPool.py`)

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `desc` | str | default='' | Description |
| `mask` | int | default=24, range 8-30 | CIDR mask |
| `range_start` | int | notnone | Start IP as integer |
| `range_end` | int | notnone | End IP as integer |
| `vlan_id` | str | notnone, FK→VLAN | Parent VLAN |

| Method | Return | Description |
|--------|--------|-------------|
| `get_by_vlan(vlan_id)` | list[IpPool] | All pools for a VLAN |
| `octetts_to_int(o1,o2,o3,o4)` | int | Convert 4 octets to integer |
| `int_to_octetts(input)` | tuple | Integer to 4-octet tuple |
| `int_to_dotted(input)` | str | Integer to dotted notation (e.g., "10.0.0.1") |
| `dotted_to_int(str_input)` | int | Dotted notation to integer |
| `mask(octetts=False, dotted=False)` | int/tuple/str | Returns subnet mask in requested format |
| `subnet_ip(octetts=False, dotted=False)` | int/tuple/str | Returns subnet address |
| `validate()` | dict errors | Validates mask range, range overlap, IP validity, VLAN purpose constraints |

**Validation Error Codes**: 30 (mask range), 31 (mask doesn't fit range), 32 (range_start > range_end), 33 (overlaps existing pool), 34 (invalid IP), 39 (only one pool allowed for VLAN purpose 1/2)

---

### Session (`backend/elements/Session.py`)

Extends `SessionBase` from noAPIframe.

| Attribute | Type | Description |
|-----------|------|-------------|
| `cookie_name` | str | `'LPOSsession'` |
| `_user_cls` | class | `Participant` |

No custom methods — inherits all CRUD and validation from SessionBase.

---

### Setting (`backend/elements/Setting.py`)

Extends `SettingBase` from noAPIframe.

**Valid Types**: `str`, `int`, `float`, `bool`, `ip` (stored as int)

| Setting Key | Type | Default | Description |
|-------------|------|---------|-------------|
| `version` | str | None | Current LPOS software version |
| `system_commited` | bool | False | Whether system config is applied to switches |
| `integrity_switchlinks` | float | 0.0 | Timestamp of last switchlink integrity check |
| `integrity_vlans` | float | 0.0 | Timestamp of last VLANs integrity check |
| `integrity_ippools` | float | 0.0 | Timestamp of last IP pools integrity check |
| `integrity_tables` | float | 0.0 | Timestamp of last tables integrity check |
| `integrity_lpos` | float | 0.0 | Timestamp of last LPOS integrity check |
| `integrity_settings` | float | 0.0 | Timestamp of last settings integrity check |
| `lpos_mgmt_mac` | str\|None | None | Cached MAC of LPOS mgmt interface |
| `lpos_mgmt_ip` | str\|None | None | Cached IP of LPOS mgmt interface |
| `server_port` | int | 8000 | Backend listen port |
| `os_nw_interface` | str | '' | Host network interface for VLAN attachment |
| `metrics_enabled` | bool | False | Enable Prometheus metrics endpoint |
| `metrics_port` | int | 8001 | Metrics listen port |
| `absolute_seatnumbers` | bool | False | Use absolute seat numbering |
| `disable_auto_commits` | bool | False | Disable automatic config commits |
| `play_ip` | ip (int) | None | LPOS IP in play network |
| `play_dhcp` | ip (int) | None | DHCP server IP in play network |
| `play_gateway` | ip (int) | None | Gateway/Router IP in play network |
| `upstream_dns` | ip (int) | None | Upstream DNS server IP |
| `domain` | str | '' | Search domain for play network |
| `subdomain` | str | '' | Subdomain for LPOS web interface |
| `nlpt_sso` | bool | False | Enable NLPT SSO login |
| `sso_login_url` | str | '' | URL to get SSO auth token |
| `sso_onboarding_url` | str | '' | URL to get SSO onboarding data |
| `sso_ip_overwrite` | ip (int)\|None | None | Skip nslookup for SSO IP
| `play_vlan_def_ip` | ip (int) | None | Default IP for new play VLAN IpPools |
| `play_vlan_def_mask` | int | 24 | Default mask for new play VLAN IpPools |
| `mgmt_vlan_def_ip` | ip (int) | None | Default IP for new mgmt VLAN IpPools |
| `mgmt_vlan_def_mask` | int | 24 | Default mask for new mgmt VLAN IpPools |
| `ob_vlan_def_ip` | ip (int) | None | Default IP for new onboarding VLAN IpPools |
| `ob_vlan_def_mask` | int | 24 | Default mask for new onboarding VLAN IpPools |

**Admin-writable settings** (from SettingEndpoint `_admin_writeable`):
`os_nw_interface`, `play_ip`, `play_dhcp`, `play_gateway`, `upstream_dns`, `domain`, `subdomain`, `absolute_seatnumbers`, `nlpt_sso`, `sso_ip_overwrite`, `sso_login_url`, `sso_onboarding_url`, `server_port`, `metrics_enabled`, `metrics_port`, `disable_auto_commits`, `haproxy_api_host`, `haproxy_api_port`, `haproxy_api_user`, `haproxy_api_pw`, `play_vlan_def_ip`, `play_vlan_def_mask`, `mgmt_vlan_def_ip`, `mgmt_vlan_def_mask`, `ob_vlan_def_ip`, `ob_vlan_def_mask`

**Readable settings** (from SettingEndpoint `_all_readable`):
`domain`, `subdomain`, `absolute_seatnumbers`, `nlpt_sso`, `sso_login_url`

---

## Endpoint/API Routes

### SwitchEndpoint (`backend/endpoints/switch.py`)

Extends `ElementEndpointBase` for CRUD on Switch.

| Route | Method | Auth | Description |
|-------|--------|------|-------------|
| `/switch/{id}/` | GET/PATCH/DELETE | Admin (CRUD) | Standard element operations |
| `/switch/commit/{id}/` | POST | Admin | Commit config to switch hardware |
| `/switch/retreat/{id}/` | POST | Admin | Retreat config from switch hardware |

**Custom Methods**:
- `commit(element_id)` — Validates session, calls `Switch.commit()`, returns 201 on success
- `retreat(element_id)` — Validates session, calls `Switch.retreat()`, returns 201 on success

---

### OnboardingEndpoint (`backend/endpoints/onboarding.py`)

Custom endpoint (not ElementEndpointBase).

| Route | Method | Auth | Description |
|-------|--------|------|-------------|
| `/onboarding/` | GET | No | Returns available tables or SSO login URL |
| `/onboarding/` | POST | No | Claims a seat with password/token |
| `/onboarding/` | PUT | No | Confirms onboarding choice, triggers port config |

**GET Response**: `{'tables': [1,2,3]}` or `{'login_url': 'https://...'}` (SSO mode)

**POST Flow**:
1. MAC-based device detection via ARP/DHCP leases
2. If already onboarded: returns IP and online status
3. If blocked: error code 7
4. SSO mode (`nlpt_sso`): validates token, fetches participant from external system
5. Local mode: validates table/seat/pw; checks pw_strikes (block after 3 failures)
6. Creates/associates Participant and Device
7. Sets `claiming_device_id` on Seat

**PUT Flow**:
1. Validates device is claiming a seat
2. If rejected: blocks device, returns error code 14
3. If accepted: sets device seat_id, triggers `device_onboarding_schedule()`

---

### ParticipantEndpoint (`backend/endpoints/participant.py`)

Extends `ElementEndpointBase` for CRUD on Participant.

| Route | Method | Auth | Description |
|-------|--------|------|-------------|
| `/participant/{id}/` | GET/PATCH/DELETE | Admin (CRUD) | Standard element operations |
| `/participant/offboard/{id}/` | PUT | Admin | Offboards participant (removes devices, clears seat) |

---

### SystemEndpoint (`backend/endpoints/system.py`)

Custom endpoint for system administration.

| Route | Method | Auth | Description |
|-------|--------|------|-------------|
| `/system/integrity?specific_check={key}` | GET | Admin | Runs all integrity checks (optional: `switchlinks`, `vlans`, `ippools`, `tables`, `lpos`, `settings`) |
| `/system/commit_interfaces` | POST | Admin | Commits VLAN OS interfaces (Docker ipvlan) |
| `/system/retreat_interfaces` | POST | Admin | Retreats VLAN OS interfaces |
| `/system/commit_dns_servers` | POST | Admin | Commits DNS servers (CoreDNS containers) |
| `/system/retreat_dns_servers` | POST | Admin | Retreats DNS servers |
| `/system/commit_dhcp_servers` | POST | Admin | Commits DHCP servers (Kea-DHCP4 containers) |
| `/system/retreat_dhcp_servers` | POST | Admin | Retreats DHCP servers |
| `/system/commit_switches` | POST | Admin | Commits all switches in restart order |
| `/system/retreat_switches` | POST | Admin | Retreats all switches in reverse order |
| `/system/commit_haproxy` | POST | Admin | Commits HAProxy config |
| `/system/retreat_haproxy` | POST | Admin | Retreats HAProxy config |
| `/system/remove_offline_devices` | POST | Admin | Removes offline devices without config/description (60s threshold) |

---

### Metrics Endpoint (`backend/endpoints/metrics.py`)

Runs as separate CherryPy process on `metrics_port`. Prometheus format.

**Metrics Exported**:
- `lpos_participants_count`, `lpos_seats_count`, `lpos_tables_count`, `lpos_devices_count`
- `lpos_vlans_count`, `lpos_switches_count`, `lpos_ippools_count`, `lpos_ports_count`, `lpos_portconfigcaches_count`
- `lpos_participants_seated`, `lpos_participants_onboarded`, `lpos_participants_extra_devices`
- `lpos_devices_managed`
- `lpos_table_seats{number,desc}`, `lpos_table_seats_onboarded{number,desc}` (per-table gauges)

---

## Helper/Utility Files

### backgroundworker.py (`backend/helpers/backgroundworker.py`)

**Background Threads**:
- `device_scanner_thread` — Runs every 15 seconds: scans all switches for ports/devices, maps new devices
- `device_onboarding_thread` — Queue-based worker: processes device/port onboarding jobs

**Key Functions**:
| Function | Description |
|----------|-------------|
| `device_scanner_scan_once()` | Single scan cycle; returns count of new devices found |
| `device_scanner()` | Infinite loop scanner (sleeps 15s between cycles) |
| `device_scanner_start()` | Starts the scanner thread if not running |
| `device_onboarding()` | Queue worker: disables port, commits switch config, updates DHCP server, re-enables port |
| `device_onboarding_start()` | Starts the onboarding thread if not running |
| `device_onboarding_schedule(device_id)` | Queues a device onboarding job (JSON: `{'device': id}`) |
| `port_onboarding_schedule(port_id)` | Queues a port onboarding job (JSON: `{'port': id}`) |

---

### client.py (`backend/helpers/client.py`)

**Network/Client Utilities**:
| Function | Description |
|----------|-------------|
| `get_client_ip()` | Returns client IP from X-Forwarded-For or remote |
| `get_client_mac(ip=None)` | MAC resolution via: DHCP leases → hostarp container → local ARP → Device DB fallback |
| `_determine_mgmt_mac_and_ip(return_ip, return_mac)` | Finds LPOS mgmt interface MAC/IP via psutil in container |
| `get_mgmt_mac()` | Cached MAC of LPOS mgmt interface (no colons) |
| `get_mgmt_ip()` | Cached IP of LPOS mgmt interface (dotted notation) |
| `nslookup(domain)` | DNS lookup via HAProxy container |
| `containerd_psutil()` | Runs psutil in a temporary Docker container with host network to get interface info |

---

### haproxy.py (`backend/helpers/haproxy.py`)

**HAProxy Management Classes**:
| Class | Container Search Name | Description |
|-------|----------------------|-------------|
| `_BaseHAproxy` | — | Base class: API session, ipvlan attach/detach, command execution |
| `LPOSHAproxy` | `'haproxy'` | Main LPOS HAProxy: sets MS redirect URL, attaches VLANs |
| `SSOHAproxy` | `'lpos-ssoproxy'` | SSO proxy: starts container with config, manages SSL termination |

**Key Methods** (inherited from `_BaseHAproxy`):
| Method | Description |
|--------|-------------|
| `container_running()` | Checks if target container is running |
| `wait_for_running(timeout=5)` | Waits for API to respond |
| `attach_ipvlan(name, int_ip)` | Connects container to ipvlan network |
| `detach_ipvlan(name)` | Disconnects from ipvlan network |
| `detach_all_ipvlans()` | Detaches from all lpos-ipvlan* networks |
| `execute_command(cmd)` | Runs command in container |

**LPOSHAproxy Specific**:
| Method | Description |
|--------|-------------|
| `set_ms_redirect_url()` | Updates HTTP request rule for Microsoft connectivity test redirect |

---

### switchmgmt.py (`backend/helpers/switchmgmt.py`)

**Switch Management Orchestration**:
| Function | Description |
|----------|-------------|
| `switch_hierarchy(start_switch=None)` | Builds dict tree of switch connections via switchlinks; starts from LPOS port |
| `switch_restart_order(start_switch=None)` | Returns list of Switch IDs in safe commit/retreat order (leaves first) |
| `switches_commit()` | Commits all switches in stages: vlans → vlan_memberships → isolation → port_vlans |
| `switches_retreat()` | Retreats all switches in reverse stages: port_vlans → isolation → vlan_memberships → vlans |

**Commit Stages**: Each stage retries failed switches once before marking as permanently failed.

---

### system.py (`backend/helpers/system.py`)

**Integrity Checking Functions**:
| Function | Description |
|----------|-------------|
| `get_open_commits()` | Count of uncommitted switches |
| `_check_integrity_switchlinks()` | Validates switchlink bidirectionality and count (N*2-2) |
| `_check_integrity_vlans()` | Checks mgmt and play VLANs exist |
| `_check_integrity_ippools()` | Checks IpPools for mgmt, onboarding VLANs |
| `_check_integrity_tables()` | Validates seats per table, IP pool sizes |
| `_check_integrity_lpos()` | Validates LPOS IP is in mgmt subnet |
| `_check_integrity_settings()` | Validates os_nw_interface, required settings (play_ip, play_dhcp, play_gateway, upstream_dns must be non-None), domain/subdomain not empty |
| `check_integrity()` | Runs all checks |
| `check_integrity_switch_commit()` | VLANs + IpPools + LPOS checks |
| `check_integrity_vlan_interface_commit()` | Settings + IpPools checks |
| `check_integrity_vlan_dns_commit()` | Settings + IpPools checks |
| `check_integrity_vlan_dhcp_commit()` | Settings + IpPools checks |
| `check_integrity_haproxy_commit()` | Settings check only |
| `remove_offline_devices()` | Deletes offline devices without config/description (60s threshold) |

**Caching**: Integrity checks are cached for 30 seconds (`check_max_diff`).

---

### vlanmgmt.py (`backend/helpers/vlanmgmt.py`)

**VLAN Server Management**:
| Function | Description |
|----------|-------------|
| `vlan_os_interfaces_commit()` | Creates Docker ipvlan networks for all VLANs |
| `vlan_os_interfaces_retreat()` | Removes all Docker ipvlan networks |
| `vlan_dns_server_commit()` | Starts CoreDNS containers for applicable VLANs |
| `vlan_dns_server_retreat()` | Stops all CoreDNS containers |
| `vlan_dhcp_server_commit()` | Starts Kea-DHCP4 containers for play/onboarding VLANs |
| `vlan_dhcp_server_retreat()` | Stops all Kea-DHCP4 containers |

---

### sso.py (`backend/helpers/sso.py`)

**SSO Integration**:
| Function | Description |
|----------|-------------|
| `nlpt_fetch_participant(token)` | Fetches participant data from external SSO system using Bearer token |

---

### versioning.py / version.py (`backend/helpers/versioning.py`, `version.py`)

**Database Migration System**:
- `version.py`: Contains current software version string (replaced by build system)
- `versioning.py`: Version comparison functions and migration logic

| Function | Description |
|----------|-------------|
| `versions_eq/lt/gte/lte/gt(left, right)` | Semantic version comparison (handles X.Y.Z.alpha1 format) |
| `run()` | Main migration entry point: compares DB version to current, runs migrations |
| `db_defaults()` | Creates default admin user if none exist |

**Migrations**:
- `< 0.2`: Added `desc` to Switch, `commit_config` to Port
- `< 0.5.1`: Added `port_numbering_offset` to Switch
- `< 0.6.1`: Migrated legacy settings collection and config.json to Setting element
- `< 0.9.0`: Removed deprecated `lpos` attribute from IpPool

---

## Frontend Components

| Component | Path | Description |
|-----------|------|-------------|
| `app-routing.module.ts` | `src/app/` | Route definitions for all screens |
| `app.component.ts/html/scss` | `src/app/` | Root component with menu and content area |
| `app.module.ts` | `src/app/` | Angular module declarations, imports |
| `devices-list/` | `components/devices-list/` | Table of all detected devices |
| `devices-screen/` | `components/devices-screen/` | Device detail/edit screen |
| `ip-pool-creadit/` | `components/ip-pool-creadit/` | Create/edit IP pool form (note: "creadit" typo) |
| `ip-pools-list/` | `components/ip-pools-list/` | Table of all IP pools |
| `login/` | `components/login/` | Login screen component |
| `logout/` | `components/logout/` | Logout button/component |
| `menu/` | `components/menu/` | Navigation menu sidebar |
| `network-screen/` | `components/network-screen/` | Network overview (VLANs, switches, ports) — commit all and retreat all buttons removed
| `onboarding/` | `components/onboarding/` | Participant onboarding flow UI with 2-minute fallback timer for online check
| `participants-list/` | `components/participants-list/` | Table of all participants |
| `participants-screen/` | `components/participants-screen/` | Participant detail/edit screen |
| `ports-list/` | `components/ports-list/` | Port configuration table |
| `seats-list/` | `components/seats-list/` | Seat management table |
| `setting-ip-field/` | `components/setting-ip-field/` | IP address input component |
| `settings-screen/` | `components/settings-screen/` | System settings screen with maintenance mode: integrity check display (overall + per-check), commit/retreat step-by-step status, offline device cleanup, port config cache monitoring |
| `switch-creadit/` | `components/switch-creadit/` | Create/edit switch form (note: "creadit" typo) |
| `switch-detail/` | `components/switch-detail/` | Switch detail view with ports |
| `switches-list/` | `components/switches-list/` | Table of all switches |
| `table-creadit/` | `components/table-creadit/` | Create/edit table form (note: "creadit" typo) |
| `tables-list/` | `components/tables-list/` | Table of all tables |
| `tables-screen/` | `components/tables-screen/` | Tables overview screen |
| `vlan-config-edit/` | `components/vlan-config-edit/` | VLAN configuration editor |
| `vlan-creadit/` | `components/vlan-creadit/` | Create/edit VLAN form (note: "creadit" typo) |
| `vlans-list/` | `components/vlans-list/` | Table of all VLANs |
| `welcome/` | `components/welcome/` | Welcome/home screen |

---

## Frontend Services

All services are `@Injectable({ providedIn: 'root' })` and use `HttpClient` with `{withCredentials: true}`.

| Service | API Base URL | Key Methods |
|---------|-------------|-------------|
| `DeviceService` | `apiUrl + '/device/'` | `getDevices()`, `getDevice(id)`, `createDevice(...)`, `updateDevice(id, ...)`, `deleteDevice(id)` |
| `IpPoolService` | `apiUrl + '/ippool/'` | `getIpPools()`, `getIpPool(id)`, `createIpPool(...)`, `updateIpPool(id, ...)`, `deleteIpPool(id)` |
| `LoginService` | `apiUrl + '/login/'` | `login(login, pw)`, `logout()` |
| `OnboardingService` | `apiUrl + '/onboarding/'` | `getOnboarding()`, `postOnboarding(data)`, `putOnboarding(data)` |
| `ParticipantService` | `apiUrl + '/participant/'` | `getParticipants()`, `getParticipant(id)`, `create(...)`, `update(id, ...)`, `delete(id)`, `offboard(id)` |
| `PortService` | `apiUrl + '/port/'` | `getPorts()`, `getPort(id)`, `create(...)`, `update(id, ...)`, `delete(id)` |
| `SeatService` | `apiUrl + '/seat/'` | `getSeats()`, `getSeat(id)`, `create(...)`, `update(id, ...)`, `delete(id)` |
| `SettingService` | `apiUrl + '/setting/'` | `getSettings()`, `getSetting(id)`, `update(id, data)` |
| `SwitchService` | `apiUrl + '/switch/'` | `getSwitches()`, `getSwitch(id)`, `create(...)`, `update(id, ...)`, `delete(id)`, `execCommit(id)`, `execRetreat(id)`, `updatePortNumberingOffset(id, pno)` |
| `SystemService` | `apiUrl + '/system/'` | `checkIntegrity(specific_check?)`, `execCommitInterfaces()`, `execRetreatInterfaces()`, `execCommitDnsServers()`, `execRetreatDnsServers()`, `execCommitDhcpServers()`, `execRetreatDhcpServers()`, `execCommitSwitches()`, `execRetreatSwitches()`, `execCommitHaproxy()`, `execRetreatHaproxy()`, `execRemoveOfflineDevices()` |
| `TableService` | `apiUrl + '/table/'` | `getTables()`, `getTable(id)`, `create(...)`, `update(id, ...)`, `delete(id)` |
| `VlanService` | `apiUrl + '/vlan/'` | `getVlans()`, `getVlan(id)`, `create(...)`, `update(id, ...)`, `delete(id)` |
| `UtilsService` | — | Utility/helper functions (no API calls) |
| `ErrorHandlerService` | — | HTTP error handling interceptor logic |

---

## TypeScript Interfaces

### Device (`src/app/interfaces/device.ts`)
```typescript
interface Device {
    id: string;
    mac: string;
    desc: string;
    seat_id: string | null;
    participant_id: string | null;
    ip_pool_id: string | null;
    ip: number | null;
    port_id: string | null;
    onboarding_blocked: boolean;
    pw_strikes: number;
    last_scan_ts: number;
    commit_config: PortCommitConfig;
    retreat_config: PortCommitConfig;
}
```

### Vlan (`src/app/interfaces/vlan.ts`)
```typescript
enum VlanPurposeType { play, mgmt, onboarding, other }
interface Vlan {
    id: string;
    number: number;
    purpose: VlanPurposeType;
    desc: string;
}
```

### Switch (`src/app/interfaces/switch.ts`)
```typescript
enum SwitchPurposeType { core, participants, mixed }
interface Switch {
    id: string;
    desc: string;
    addr: string;
    user: string;
    pw: string;
    purpose: SwitchPurposeType;
    commited: boolean;
    onboarding_vlan_id: string | null;
    connected: boolean;
    mac: string;
    known_vlans: string[];
    port_numbering_offset: number;
}
```

### Seat (`src/app/interfaces/seat.ts`)
```typescript
interface Seat {
    id: string;
    number: number;
    number_absolute: number;
    pw: string | null;
    table_id: string;
}
```

### Participant (`src/app/interfaces/participant.ts`)
```typescript
interface Participant {
    id: string;
    admin: boolean;
    name: string;
    login: string | null;
    pw: string | null;
    seat_id: string | null;
}
```

### Table (`src/app/interfaces/table.ts`)
```typescript
interface Table {
    id: string;
    number: number;
    desc: string;
    switch_id: string;
    seat_ip_pool_id: string;
    add_ip_pool_id: string;
}
```

### Port (`src/app/interfaces/port.ts`)
```typescript
interface PortCommitConfig {
    vlans: string[];
    default: string;
    enabled: boolean;
    mode: string;
    receive: string;
    force: boolean;
}
interface PortConfigCache {
    id: string | undefined;
    port_id: string | undefined;
    scope: number | undefined;
    device_desc: string;
    isolate: boolean;
    vlan_ids: string[];
    default_vlan_id: string | null;
    enabled: boolean;
    mode: string;
    receive: string;
    force: boolean;
}
interface Port {
    id: string;
    number: number;
    number_display: number;
    desc: string;
    switch_id: string;
    participants: boolean;
    switchlink: boolean;
    switchlink_port_id: string | null;
    commit_disabled: boolean;
    retreat_disabled: boolean;
    commit_config: any | null;
    retreat_config: any | null;
    vlan_ids: string[];
    default_vlan_id: string | null;
    type: string;
    enabled: boolean;
    link: boolean;
    speed: string;
    receive: string;
    calculated_commit_config: PortConfigCache;
    calculated_retreat_config: PortConfigCache;
}
```

### IpPool (`src/app/interfaces/ip-pool.ts`)
```typescript
interface IpPool {
    id: string;
    desc: string;
    mask: number;
    range_start: number;
    range_end: number;
    vlan_id: string;
}
```

### Setting (`src/app/interfaces/setting.ts`)
```typescript
interface Setting {
    id: string;
    type: string;
    value: any;
    desc: string;
    order: number;
    ro: boolean;
}
```

### Onboarding (`src/app/interfaces/onboarding.ts`)
```typescript
interface Onboarding {
    ip?: number;
    tables?: number[];
    participant?: string;
    done?: boolean;
    login_url?: string;
    online?: boolean;
}
```

### Login (`src/app/interfaces/login.ts`)
```typescript
interface Login {
    session_id?: string;
    till?: number;
    complete?: boolean;
}
```

---

## Startup/Boot Sequence

1. **Docker Compose** starts all services in dependency order
2. **Prefetcher** (runs once, then exits): Pulls Docker images (alpine, python:3.10-alpine, haproxy, coredns, kea-dhcp4)
3. **Backend main.py**:
   a. Connects to MongoDB (`docDB.wait_for_connection()`)
   b. Runs versioning/migrations (`versioning_run()`)
   c. Clears cached LPOS mgmt MAC/IP
   d. Starts background worker threads (`device_onboarding_start()`)
   e. Starts metrics exporter process (if enabled)
   f. If `disable_auto_commits` is False:
      - Runs integrity check
      - If SSO enabled: starts SSO HAProxy container, sets up IP
      - Sets MS redirect URL on LPOS HAProxy
      - Commutes VLAN OS interfaces
      - Commits DNS servers
      - Commits DHCP servers
   g. Starts CherryPy server

4. **Scanner** (separate container):
   a. Calls `device_onboarding_start()` to sync threads
   b. Enters infinite loop: scan every 15 seconds

---

## Key File Paths Reference

### Backend Entry Points
- `backend/main.py` — Main API server
- `backend/scanner.py` — Device scanner entry point
- `backend/prefetcher.py` — Docker image prefetcher

### Backend Elements (Models)
- `backend/elements/__init__.py` — Exports all element classes
- `backend/elements/VLAN.py` — VLAN model with Docker network management
- `backend/elements/Switch.py` — Switch model with SSH communication
- `backend/elements/Device.py` — Device tracking and IP assignment
- `backend/elements/Seat.py` — Seat management within tables
- `backend/elements/Table.py` — Table (switch + pools) configuration
- `backend/elements/Participant.py` — User/participant model
- `backend/elements/Port.py` — Switch port configuration
- `backend/elements/PortConfigCache.py` — Auto-generated port config cache
- `backend/elements/IpPool.py` — IP address pool management
- `backend/elements/Session.py` — Session management
- `backend/elements/Setting.py` — System settings store

### Backend Endpoints (API)
- `backend/endpoints/__init__.py` — Exports all endpoint classes
- `backend/endpoints/system.py` — System administration endpoints
- `backend/endpoints/switch.py` — Switch CRUD + commit/retreat
- `backend/endpoints/onboarding.py` — Participant onboarding flow
- `backend/endpoints/participant.py` — Participant CRUD + offboard
- `backend/endpoints/metrics.py` — Prometheus metrics exporter

### Backend Helpers
- `backend/helpers/backgroundworker.py` — Device scanner and onboarding threads
- `backend/helpers/client.py` — Network client utilities (IP/MAC resolution)
- `backend/helpers/haproxy.py` — HAProxy container management
- `backend/helpers/switchmgmt.py` — Switch commit/retreat orchestration
- `backend/helpers/system.py` — Integrity checking functions
- `backend/helpers/vlanmgmt.py` — VLAN server (DNS/DHCP) management
- `backend/helpers/sso.py` — SSO integration
- `backend/helpers/versioning.py` — Database migration system
- `backend/helpers/version.py` — Current version string

### Frontend Entry Points
- `frontend/src/main.ts` — Angular bootstrap
- `frontend/src/app/app.module.ts` — Root module
- `frontend/src/app/app-routing.module.ts` — Route definitions
- `frontend/src/app/app.component.ts/html/scss` — Root component

### Frontend Services (14 services)
- `frontend/src/app/services/*.ts` — All API service files

### Frontend Interfaces (11 interfaces)
- `frontend/src/app/interfaces/*.ts` — All TypeScript interface definitions

### Frontend Components (26 components)
- `frontend/src/app/components/*/` — All component directories

### Infrastructure
- `docker-compose.yml` — Service orchestration
- `backend/config.json` — MongoDB host, server port, metrics config
- `haproxy/` — Custom HAProxy Docker image (Dockerfile + config + Lua scripts)
- `frontend/Dockerfile` — Angular build + Nginx serving

### Documentation
- `docs/dev.md` — Development documentation
- `docs/error-codes.md` — Error code reference
- `docs/elements_attributes.md` — Element attribute reference
- `docs/system_settings.md` — System settings reference
- `docs/switch_stats.md` — Switch statistics
- `docs/api.drawio` / `docs/login_sequence.drawio` / `docs/onboarding_sequences.md` — Architecture diagrams

### HWSwitch Module (MikroTik Communication)
- `backend/HWSwitch/` — MikroTik RouterOS SSH communication module
  - `AutoDetectSwitch` — Auto-detects switch type and provides unified API
  - Handles VLAN operations, port management, host scanning via SSH
