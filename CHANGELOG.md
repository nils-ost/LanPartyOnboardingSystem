# LPOS Changelog

## v0.4.0

  * It's now possible to set absolute seatnumbers, which results in the possibility to omit the tablenumber during onboarding
  * Replaced dnsmasq with coredns and kea-dhcp, which are started in containers
  * Device elements now have a timestamp with the last time they where discovered by a device-scan
    * according to this information all Devices with a delta-t more than 60 seconds, get marked red in the frontend
  * It's now possible to use nlpt.online as the Participant-verification backend, during the NLPT-Events, instead of LPOS own onboarding credentials
