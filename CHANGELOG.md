# LPOS Changelog

## v0.7.0

  * Settings screen does now have a button to remove all links between Devices and Ports
  * Bugfix: Commiting a single Switch now leaves out the switchlinks-integrity check, which makes it possible to commit without all Switches running
  * New Setting-Element to unify settings handling
    * Moved all settings and config variables to this Element
    * New corresponding Endpoint, that is now use by Frontend
    * New section in Settings-Screen to be able to modify all settings
  * Reworked System-Endpoint to not expose settings indirectly

## v0.6.0

  * Switch is now able to carry a port_numbering_offset, which is used on Port to calculate a port-number to display on the Frontend
  * Bugfix: With multiple Devices on a Port, if only a single Device does have a manual config, this is applied now in PortConfigCache
  * It's now possible to remove all offline Devices, that are not referenced by anything, with one click
  * There is now a button, in Devices list, to remove the attched Port from Device
  * Device description is now displayed in PortList, if Port does not have a description
  * Participant name is copied to Device description for Devices related to Participants
  * Before opening PortList of Switch, the current Port-states are fetched from hardware

## v0.5.0

  * It's now possible to alter the behavior of how switch-Ports are configured during commit and retreat
    * On Port-level:
      * Directly on this level, via the Network->Switch-Port interface
    * On Device-level:
      * In the Devices interface it's possible to alter the configuration for discovered devices; this configuration is than applied to the Port where the Device is connected to
    * The options are:
      * auto (the configuration is determined by LPOS)
      * disable (the switch-Port is left untouched; not available on Device-level)
      * manual (the configuration can be set manual via the frontend)
  * Reworked exported Metrics
    * removed all Switch in depth metrics, as they are better delivered by SNMP
    * added different counter metrics of LPOS objects
  * Seat-number is now validated to not exceed Tables IpPool
  * Adding and Deleting Seats with specific Number is now possible in frontend
  * Moved Device-Scanner to it's own Service
  * Devices-Screen now sortable by last_scan_ts
  * Devices-Screen can now be filtered by a Switch-Port
  * ElementEndpointBase is now capable to delete all Elements at once (not just one specific)

## v0.4.0

  * It's now possible to set absolute seatnumbers, which results in the possibility to omit the tablenumber during onboarding
  * Replaced dnsmasq with coredns and kea-dhcp, which are started in containers
  * Device elements now have a timestamp with the last time they where discovered by a device-scan
    * according to this information all Devices with a delta-t more than 60 seconds, get marked red in the frontend
  * It's now possible to use nlpt.online as the Participant-verification backend, during the NLPT-Events, instead of LPOS own onboarding credentials
