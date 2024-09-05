# LPOS Changelog

## v0.x.0

  * On Port-level, it's now possible to alter the behavior of how switch-Ports are configured during commit and retreat, the options are:
    * auto (the configuration is determined by LPOS)
    * disable (the switch-Port is left untouched)
    * manual (the configuration can be set manual via the frontend)

## v0.4.0

  * It's now possible to set absolute seatnumbers, which results in the possibility to omit the tablenumber during onboarding
  * Replaced dnsmasq with coredns and kea-dhcp, which are started in containers
  * Device elements now have a timestamp with the last time they where discovered by a device-scan
    * according to this information all Devices with a delta-t more than 60 seconds, get marked red in the frontend
  * It's now possible to use nlpt.online as the Participant-verification backend, during the NLPT-Events, instead of LPOS own onboarding credentials
