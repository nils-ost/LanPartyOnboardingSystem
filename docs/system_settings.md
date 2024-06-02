# System & Settings

## System Endpoint

| setting               | type | admin | user | desc |
| :-------------------- | :--: | :---: | :--: | :--- |
| commited              | bool |  ro   |  --  |  |
| open_commits          | bool |  ro   |  --  |  |
| seatnumbers_absolute  | bool |  rw   |  ro  |  |
| nlpt_sso              | bool |  rw   |  ro  |  |
| version               | str  |  ro   |  ro  |  |

## Setting(s) Endpoint

| setting               | type | admin | user | desc |
| :-------------------- | :--: | :---: | :--: | :--- |
| version               | str  |  ro   |  --  |  |
| os_nw_interface       | str  |  rw   |  --  |  |
| play_dhcp             | str  |  rw   |  ro  |  |
| play_gateway          | str  |  rw   |  ro  |  |
| upstream_dns          | str  |  rw   |  ro  |  |
| domain                | str  |  rw   |  ro  |  |
| subdomain             | str  |  rw   |  ro  |  |
| absolute_seatnumbers  | bool |  rw   |  ro  |  |
| nlpt_sso              | bool |  rw   |  ro  |  |
| sso_login_url         | str  |  rw   |  ro  |  |
| sso_onboarding_url    | str  |  rw   |  --  |  |
| system_commited       | bool |  ro   |  --  |  |
| integrity_ippools     | float|  ro   |  --  |  |
| integrity_lpos        | float|  ro   |  --  |  |
| integrity_settings    | float|  ro   |  --  |  |
| integrity_switchlinks | float|  ro   |  --  |  |
| integrity_tables      | float|  ro   |  --  |  |
| integrity_vlans       | float|  ro   |  --  |  |
