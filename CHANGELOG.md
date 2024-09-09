# LPOS Changelog

## v0.x.0

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

## v0.4.0

  * It's now possible to set absolute seatnumbers, which results in the possibility to omit the tablenumber during onboarding
  * Replaced dnsmasq with coredns and kea-dhcp, which are started in containers
  * Device elements now have a timestamp with the last time they where discovered by a device-scan
    * according to this information all Devices with a delta-t more than 60 seconds, get marked red in the frontend
  * It's now possible to use nlpt.online as the Participant-verification backend, during the NLPT-Events, instead of LPOS own onboarding credentials
