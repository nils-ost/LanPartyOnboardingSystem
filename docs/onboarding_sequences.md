# Onboarding Sequences

## Setup before the LAN-Party starts

The Orgs-Team needs to prepare LPOS (LanPartyOnboardingSystem) following steps are mandatory:

  * Switches/VLANs and IpPools need to be defined
  * Tables needs to be created with their corresponding IpPools
  * Seats are added to Tables, Seats do have a Password
  * Participants are created (at this point only the name of a Participant is relevant, they don't need to have a login-name or password)
  * Participants are linked to Seats (every Seat can host one Participant, the Seats determine the main Device of a Participant)

Finally every Seat should be prepared with a handout. This handout should contain at least the following information:

  * Wich website to open, to start the onboarding
  * The number of the Table
  * The number of the Seat
  * The Password corresponding to this Seat

## Onboarding of a Participant during the LAN-Party

  * The Participant sets up it's PC, and connects it to a random switchport
  * On the handout he finds the URL that he needs to open for doing the handout
  * At this point LPOS allready detected the Device of the Participant, as it knows, that the Participant is not yet onboarded it asks for the Table- and Seat-Number with the Seat-Password
  * The Participant enters this information
  * If the information are valid, the Divice is linked to the Seat. (The Password of the Seat is invalidated in this step, as a Seat is only allowed to be used for one Device)
  * This starts the process of unlocking the switch-port and assigns the predefined IP to the Device

At this point the Participant, or more specific the PC of the Participant, if fully functional and onboarded to the LAN-Party.

Also: if the Participant reopens the onboarding-website he is automatically logged in. This is because he is authenticated through it's Device. The Switch, Switch-Port, Device-MAC and Device-IP are a unique combination, that identify exactly one Participant.

## Onboarding additional Devices of Participants

It might happen, that a Participant likes to use multiple Devices on a LAN-Party. For example if he hosts a Clan-Server or something similar.

In this case he just occupies one Seat, but the Seat-Onboarding is allready used by it's main PC. But there is a solution to this problem.

  * With his main PC, that is allready onboarded, he visits the onboarding website
  * Here he is asked if he likes to create a login (remember the identification is done thorough it's main PC at this point)
  * The Participant can now give himself a login-name and password
  * On the second PC (or Server) he can now also open the onboarding website
  * Here is an option to do a onboarding through a login, this one should now be selected
  * The Participant enters his credentials, et voila the second PC (or Server) now also gets access to the network, and get a free IP assigned

Just in case the second PC (or Server) does not come with a Webbrowser, or setting up DHCP on this machine is not a valid option. The Orga-Team does have the option to link the second PC to the Participant and unlock it from the admin-panel
