# LPOS — Copilot Instructions (Shared Context)

## Project Overview

**LanPartyOnboardingSystem (LPOS)** — A DHCP-based network onboarding system for LAN parties that assigns a **defined IP per participant/seat** using MikroTik switches, Docker-managed VLANs, and dynamic DNS/DHCP servers. Participants connect to isolated switchports, onboard via a web portal, then receive their seat-assigned IP when the port is unlocked.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend   │────▶│    HAProxy   │────▶│   Backend   │
│  Angular 15  │◀────│  :80 / :8404 │◀────│ CherryPy +  │
│  PrimeNG UI  │     │  (reverse)   │     │ MongoDB     │
└─────────────┘     └──────────────┘     └─────────────┘
                                              │
                    ┌─────────────────────────┼──────────────────────────┐
                    ▼                         ▼                          ▼
              ┌───────────┐          ┌──────────────┐            ┌─────────────┐
              │  Scanner   │          │  Prefetcher  │            │ MikroTik    │
              │ (background│          │ (one-shot)   │            │ Switches    │
              │  thread)   │          └──────────────┘            │ (SSH/API)   │
              └───────────┘                                        └─────────────┘
                    │                                                    │
              ┌─────▼────────────────────────────────────────────────────▼───────┐
              │  Docker Host — ipvlan networks, CoreDNS containers, Kea-DHCP4    │
              │  containers, LPOS-HAproxy container, SSO-HAproxy container        │
              └──────────────────────────────────────────────────────────────────┘
```

## Docker Services (docker-compose.yml)

| Service | Image | Purpose | Ports |
|---------|-------|---------|-------|
| `backend` | nilsost/lpos-backend | REST API server (CherryPy) | 8001 (metrics) |
| `scanner` | nilsost/lpos-backend (cmd: scanner.py) | Background device scanning thread | — |
| `prefetcher` | nilsost/lpos-backend (cmd: prefetcher.py) | One-shot Docker image pre-fetch | — |
| `frontend` | nilsost/lpos-frontend | Angular SPA served by Nginx | — |
| `haproxy` | custom (Dockerfile) | Reverse proxy + stats | 80, 8404 (metrics) |
| `mongodb` | mongo:4.4 | Document database | — |
| `hostarp` | alpine (sleep) | ARP table sharing via host network | — |

## Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.10, CherryPy, noAPIframe (custom ORM), PyMongo |
| **Frontend** | Angular 15, PrimeNG 15, RxJS, TypeScript 4.9 |
| **Database** | MongoDB 4.4 (LPOS database) |
| **Infra** | Docker, ipvlan networks, HAProxy, CoreDNS, Kea-DHCP4 |
| **Switches** | MikroTik RouterOS (SSH via SSHClient from HWSwitch module) |

## Backend Conventions

- **Framework**: CherryPy with `@cherrypy.expose()`, `@cherrypy.tools.json_in/out()` decorators
- **ORM**: noAPIframe — all models extend `ElementBase` with `_attrdef = dict(...)` and `_id` for MongoDB ObjectId
- **Auth**: Cookie-based sessions (`LPOSsession`), `Session.validate_base()`, `session.admin()` check
- **CORS**: cherrypy-cors installed globally, preflight handled per-endpoint
- **Error codes**: Integer codes (e.g., 10–95) with descriptive messages in validation errors
- **Auto-commits**: On startup, VLAN/DHCP/DNS configs are committed unless `disable_auto_commits` is set

## Frontend Conventions

- **Framework**: Angular 15 standalone-ish modules (`app.module.ts`, `app-routing.module.ts`)
- **UI Library**: PrimeNG (data tables, forms, dialogs)
- **State**: Services with RxJS `Observable` return types; HTTP calls via `HttpClient` with `{withCredentials: true}`
- **API base URL**: from `environment.apiUrl` in `environments/environment.ts`

## Core Domain Model (High Level)

```
VLAN ─┬─ purpose: 0=play, 1=mgmt, 2=onboarding, 3=other
      └── IpPool[] (range_start, range_end, mask)

Switch ─┬─ addr, user, pw, purpose (0=core, 1=participants, 2=mixed)
        ├── onboarding_vlan_id → VLAN
        └── Port[] ─┬─ number, switchlink, participants
                      ├── commit_config / retreat_config
                      └── switchlink_port_id ↔ Port

Table ─┬─ number, switch_id → Switch
       ├── seat_ip_pool_id → IpPool (play network)
       └── add_ip_pool_id → IpPool (additional devices)

Seat ─┬─ number, number_absolute, pw
      ├── table_id → Table
      └── claiming_device_id → Device

Participant ─┬─ login, name, pw, admin
             ├── seat_id → Seat (unique FK)
             └── Session[]

Device ─┬─ mac (unique), ip (int), last_scan_ts
        ├── seat_id / participant_id (FKs)
        ├── port_id → Port
        ├── commit_config / retreat_config
        └── onboarding_blocked, pw_strikes
```

## Key Routes

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/login/` | GET/POST | Login flow (noAPIframe base) | No |
| `/logout/` | POST | Logout (noAPIframe base) | Yes |
| `/setting/` | CRUD | System settings (noAPIframe base) | Admin |
| `/vlan/` | CRUD | VLAN management (noAPIframe base) | Admin |
| `/ippool/` | CRUD | IP pool management (noAPIframe base) | Admin |
| `/table/` | CRUD | Table management (noAPIframe base) | Admin |
| `/seat/` | CRUD | Seat management (noAPIframe base) | Admin |
| `/participant/` | CRUD + `offboard()` | Participant mgmt | Admin for offboard |
| `/device/` | CRUD | Device tracking (noAPIframe base) | Admin |
| `/port/` | CRUD | Port config (noAPIframe base) | Admin |
| `/switch/` | CRUD + `commit()`, `retreat()` | Switch mgmt | Admin for commit/retreat |
| `/onboarding/` | GET/POST/PUT | Participant onboarding flow | No (MAC-based) |
| `/system/integrity?specific_check={key}` | GET | System integrity check (optional: `switchlinks`, `vlans`, `ippools`, `tables`, `lpos`, `settings`) | Admin |
| `/system/commit_interfaces` | POST | Commit VLAN OS interfaces | Admin |
| `/system/retreat_interfaces` | POST | Retreat VLAN OS interfaces | Admin |
| `/system/commit_dns_servers` | POST | Commit DNS servers | Admin |
| `/system/retreat_dns_servers` | POST | Retreat DNS servers | Admin |
| `/system/commit_dhcp_servers` | POST | Commit DHCP servers | Admin |
| `/system/retreat_dhcp_servers` | POST | Retreat DHCP servers | Admin |
| `/system/commit_switches` | POST | Commit all switches | Admin |
| `/system/retreat_switches` | POST | Retreat all switches | Admin |
| `/system/commit_haproxy` | POST | Commit HAProxy config | Admin |
| `/system/retreat_haproxy` | POST | Retreat HAProxy config | Admin |
| `/system/remove_offline_devices` | POST | Remove offline devices without config/description (60s threshold) | Admin |
| `/metrics` | GET | Prometheus metrics | No |

## Important Gotchas / Anti-Patterns

1. **VLAN purposes are mutually exclusive**: Only one VLAN each for purpose 0 (play) and 1 (mgmt). Purpose 2 (onboarding) can have multiple (one per switch).
2. **Switchlink ports must be bidirectional**: Port A's `switchlink_port_id` → Port B, and Port B's `switchlink_port_id` → Port A. Integrity checks enforce this.
3. **IPs are stored as integers**, not dotted strings — use `IpPool.int_to_dotted()` / `dotted_to_int()`.
4. **PortConfigCache is auto-generated**: Never write directly; delete by port and it regenerates on read (`scope=0` for commit, `scope=1` for retreat).
5. **Auto-commits can be disabled** via `disable_auto_commits` setting — all background workers skip work when this is true.
6. **HWSwitch module**: MikroTik communication happens through the `HWSwitch/` directory's `AutoDetectSwitch` class — never call SSH directly from elements/endpoints.
7. **Global state in Switch.py**: `switch_objects = dict()` and `switch_macs = list()` are module-level caches — they persist across requests.
