# element save/create error-codes

## generic

  * **1**: marked as not to be None
  * **2**: marked as unique, but element with value <value\> allready present
  * **3**: needs to be of type <type\> [or None]

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
  * **32***(range_start|range_end)*: needs to be smaller than range_end
  * **33***(range_start|range_end)*: overlaps with existing IpPool
  * **34***(range_start|range_end)*: not a valid IP
  * **35***(vlan_id)*: There is no VLAN with id '<vlan_id\>'

## table

  * **40***(number)*: needs to be bigger or equal to zero
  * **41***(switch_id|seat_ip_pool_id|add_ip_pool_id)*: There is no <Switch|IpPool\> with id '<switch_id|seat_ip_pool_id|add_ip_pool_id\>'
  * **42***(switch_id)*: Purpose of Switch needs to be 1 or 2
  * **43***(seat_ip_pool_id|add_ip_pool_id)*: VLAN of IpPool needs to be of purpose 0 (play/seats)
  * **44***(seat_ip_pool_id|add_ip_pool_id)*: allready in use as <add_ip_pool_id|seat_ip_pool_id\> on different Table
  * **45***(seat_ip_pool_id|add_ip_pool_id)*: can't be the same as <add_ip_pool_id|seat_ip_pool_id\>

## seat

  * **50***(table_id)*: There is no Table with id '<table_id\>'
  * **51***(number)*: needs to be 1 or bigger
  * **52***(number)*: needs to be unique per Table

## device

  * **60***(seat_id|participant_id|ip_pool_id)*: There is no <SeatParticipant|IpPool\> with id '<seat_id|participant_id|ip_pool_id\>'
  * **61***(ip_pool_id)*: Because Participant is set, Purpose of IpPools VLAN needs to be 0 (play)
  * **62***(ip_pool_id)*: is used as seat_IpPool on Table and not allowed to be used directly by Device
  * **63***(ip)*: can only be set if IpPool is set
  * **64***(ip)*: not in range of IpPool

## participant

  * **70***(seat_id)*: There is no Seat with id '<seat_id\>'

## session

  * **80***(participant_id)*: There is no Participant with id '<participant_id\>'
  * **81***(till)*: needs to be in the future
  * **82***(ip)*: does not match with the IP of request

# element delete error-codes

  * **1**: at least one IpPool is using this <element_type\>
  * **2**: at least one Table is using this <element_type\>
  * **3**: at least one Seat is uning this <element_type\>
