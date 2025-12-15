# element save/create error-codes

## generic - from noAPIframe

  * **1**: *[ElementBase]* marked as not to be None
  * **2**: *[ElementBase]* marked as unique, but element with value "<value\>" allready present
  * **3**: *[ElementBase]* needs to be of type <type\>[ or None]
  * **4**: *[ElementBase]* there is no <element-name\> with id '<element-id\>'
  * **5**: *[any]* needs to be one of: <list-of-valid-values\>
  * **6**: *[any]* not allowed to be empty
  * **7**: *[any]* generic range error like: needs do be bigger/smaller/in range...

## Session(Base) - from noAPIframe

*reserved range **1x** for individual errors*

  * **4**: *(user_id)* there is no User with id '<element-id\>'
  * **10**: *(till)* needs to be in the future
  * **11**: *(ip)* does not match with the IP of request

## Setting(Base) - from noAPIframe

*reserved range **2x** for individual errors*

  * **3**: *(value)* needs to be of type <choosen-type\> or None
  * **5**: *(type)* needs to be one of: [str, int, float, bool]

## vlan

  * **10***(number)*: needs to be a value from 1 to 1024
  * **11***(purpose)*: needs to be 0, 1, 2 or 3
  * **12***(purpose)*: values 0 and 1 need to be unique, but element with value <value\> allready present

## switch

  * **20***(purpose)*: needs to be 0, 1 or 2
  * **21***(onboarding_vlan_id)*: can't be None for purposes 1 and 2
  * **22***(onboarding_vlan_id)*: There is no VLAN with id '<vlan_id\>'
  * **23***(onboarding_vlan_id)*: VLAN purpose needs to be 2 (onboarding) but is '<vlan_purpose\>'
  * **24***(onboarding_vlan_id)*: This VLAN is allready used on a switch as onboarding_vlan

## ippool

  * **30***(mask)*: needs to be between 8 and 30
  * **31***(mask)*: does not fit to range_start and range_end
  * **32***(range_start|range_end)*: needs to be smaller than or equal to range_end
  * **33***(range_start|range_end)*: overlaps with existing IpPool
  * **34***(range_start|range_end)*: not a valid IP
  * **35***(vlan_id)*: There is no VLAN with id '<vlan_id\>'
  * **39***(vlan_id)*: Only one IpPool for VLAN with purpose of '<purpose number\>' is allowed

## table

  * **40***(number)*: needs to be bigger or equal to zero
  * **41***(switch_id|seat_ip_pool_id|add_ip_pool_id)*: There is no <Switch|IpPool\> with id '<switch_id|seat_ip_pool_id|add_ip_pool_id\>'
  * **42***(switch_id)*: Purpose of Switch needs to be 1 or 2
  * **43***(seat_ip_pool_id|add_ip_pool_id)*: VLAN of IpPool needs to be of purpose 0 (play/seats)
  * **44***(seat_ip_pool_id)*: allready in use as add_ip_pool_id on different Table
  * **45***(seat_ip_pool_id|add_ip_pool_id)*: can't be the same as <add_ip_pool_id|seat_ip_pool_id\>
  * **46***(add_ip_pool_id)*: allready in use as seat_ip_pool_id on different Table

## seat

  * **50***(table_id)*: There is no Table with id '<table_id\>'
  * **51***(number)*: needs to be 1 or bigger
  * **52***(number)*: needs to be unique per Table
  * **53***(number_absolute)*: needs to be 0 or bigger
  * **54***(number)*: is exceeding Tables IpPool range

## device

  * **60***(seat_id|participant_id|ip_pool_id|port_id|commit_config.vlans|retreat_config.vlans|commit_config.default|retreat_config.default)*: There is no <Seat|Participant|IpPool|Port|VLAN\> with id '<seat_id|participant_id|ip_pool_id|port_id|vlan_id\>'
  * **61***(ip_pool_id)*: Because Participant is set, Purpose of IpPools VLAN needs to be 0 (play)
  * **62***(ip_pool_id)*: is used as seat_IpPool on Table and not allowed to be used directly by Device
  * **63***(ip)*: can only be set if IpPool is set
  * **64***(ip)*: not in range of IpPool
  * **65***(commit_config.mode|commit_config.receive)*: needs to be one of <list of some values\> but is <value\>
  * **66***(commit_config.vlans)*: at least one vlan is required

## participant

  * **70***(seat_id)*: There is no Seat with id '<seat_id\>'

## port

  * **90***(switch_id|switchlink_port_id|commit_config.vlans|retreat_config.vlans|commit_config.default|retreat_config.default)*: There is no <Switch|Port|VLAN\> with id '<switch_id|switchlink_port_id|vlan_id\>'
  * **91***(number)*: Needs to be 0 or bigger
  * **92***(number)*: Needs to be unique per Switch
  * **93***(switchlink_port_id)*: The Port '<switchlink_port_id\>' is not declared as a switchlink
  * **94***(commit_config.mode|commit_config.receive)*: needs to be one of <list of some values\> but is <value\>
  * **95***(commit_config.vlans)*: at least one vlan is required

# element delete error-codes

  * **1**: at least one IpPool is using this <element_type\>
  * **2**: at least one Table is using this <element_type\>
  * **3**: at least one Seat is using this <element_type\>
  * **4**: at least one Switch is uning this <element_type\>

# switchs_commit/_retreat error-codes

  * **1**: system integrity check failed *additional parameter `integrity` containing the result dict of check_integrity*
  * **2**: missing Switches in restart order *additional parameter `missing` with list of missing Switch-IDs*
  * **3**: to many Switches in restart order
  * **4**: not all Switches could be <commited|retreated\> *additional parameter `failed` with list of Switch-IDs where commit/retreat failed*

# vlan_os_interfaces_commit/_retreat error-codes

  * **1**: system integrity check failed *additional parameter `integrity` containing the result dict of check_integrity*
  * **2**: not all VLAN OS-Interfaces could be <commited|retreated\> *additional parameter `failed` with list of Switch-IDs where commit/retreat failed*

# vlan_dnsmasq_config_commit/_retreat error-codes

  * **1**: system integrity check failed *additional parameter `integrity` containing the result dict of check_integrity*
  * **2**: not all VLAN dnsmasq-configs could be <commited|retreated\> *additional parameter `failed` with list of Switch-IDs where commit/retreat failed*

# system check_integrity error-codes

  * **1**: there is a missmatch in how many switchlinks should exist (<count\>) and do exist (<count\>)
  * **2**: the following switchlinks do not have a switchlink target defined: <list of Port-IDs\> *additional parameter `nones` with list of Port-IDs without a switchlink target*
  * **3**: the following ports are used as switchlink targets multiple times: <list of Port-IDs\> *additional parameter `multiuse` with list of Port-IDs that are used multiple times as a target*
  * **4**: the following ports are not reflected by their switchlink targets: <list of Port-IDs\> *additional parameter `not_reflecting` with list of Port-IDs that are not reflected by their targets*
  * **5**: mgmt-VLAN is missing
  * **6**: IpPool for mgmt-VLAN is missing
  * **7**: IP of LPOS server could not be determined
  * **8**: IP of LPOS server is not in the same subnet as mgmt-IpPool
  * **9**: setting '<name\>' is not defined, but it's needed
  * **10**: invalid hw-interface name '<name\>'
  * **11**: invalid path '<path\>'
  * **12**: play-VLAN is missing
  * **14**: IpPool for onboarding VLAN '<number\>: <desc\>' is missing
  * **15**: no Seats present for Table '<number\>: <desc\>'
  * **16**: not enough IPs in play-IpPool '<desc\>' for Table '<number\>: <desc\>'
  * **17**: not enough IPs in onboarding-IpPool '<desc\>' for Table '<number\>: <desc\>'
  * **18**: Seat <number\> of Table '<number\>: <desc\>' is missing number_absolute
  * **19**: nlpt_sso is enabled but absolute_seatnumbers is disabled
  * **20**: setting '<name\>' is not allowed to start or end with . (dot)

# onboarding error-codes

  * **1**: method not allowed
  * **2**: Submitted data need to be of type dict
  * **3**: data is needed to be submitted
  * **4**: <something\> is missing in data
  * **5**: <something\> must be of type <whatever\>
  * **6**: could not determine device
  * **7**: device is blocked for onboarding
  * **8**: invalid table number
  * **9**: invalid seat number
  * **10**: seat is allready taken
  * **11**: wrong password
  * **12**: Seat is not associated to a Participant
  * **13**: missing steps
  * **14**: contact admin
  * **15**: could not fetch Participant data from SSO system
  * **16**: you are on the wrong table
