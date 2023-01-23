# LanPartyOnboardingSystem

## The Idea

When onboarding LanParty Participants we discoverd that they sometimes forget to set the correct DNS or Gateway IP, or select the entirely wrong IP in their static networkconfiguration.

Instead of using static IP-Configuration it would be possible to run a DHCP-Server and let this one configure the Participant network. But there is a benefit of Participants (or better said Seats) to have a defined IP-Address for match-making. A DHCP Server would promote random IPs.

For this reason the idea of LanPartyOnboardingSystem came to mind; A DHCP Server is configuring the Participant network, but enforces a defined IP per Participant/Seat. Or in some more detail:  
A Participant arrives at the LanParty locations, sets up it's PC on a defined Seat and connects to a random Switchport. The participant is now in an isolated networkenvironment. He gets an random IP in an onboarding-network, that is only allowed to communicate to the onboarding server (this can be done through some VLAN and portisolation settings on the switches). The onboarding server now presents a webpage to the participant. Here he can login with his seatnumber and/or participant account. Now that the server knows hwo he is, on which seat he is placed and which networkport he occupies; a static DHCP entry in the play-network is configured. After that the corresponding switchport is unlocked to communicate to the play-network and ist restared; with restarting the network port (disable/enable cycle) the participant PC is forced to ask for a new DHCP-Lease and should now get it's defined (seat-based) IP-Address.

## Limitations

  * managed switches are required, it's not possible to have a single unmanaged switch on the network
  * as we are using MikroTik Switches on our LanPartys the application is currently designed around those and not compatible with other vendors
  * currently the development is in the design-pahse, it's going to take at least until May 2023 till there is some kind of working system