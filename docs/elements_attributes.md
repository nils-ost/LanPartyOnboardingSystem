# Detailed information about Element-Attributes

## Port.commit_config

This attribute can be None or dict()

If it is None, this means the Port is configured automatically, if it is a dict() the config contained in the dict() is wirten to port on commit.

### possible attributes in dict()

  * **vlans** *(list(str))*: list of VlanIds this Port has access to. Must contain at least one VlanId
  * **default** *(str)*: defines the VLAN(tag) that is given to untagged traffic on this port. If it is not explicitly set, the first entry of vlans is assigned
  * **enabled** *(bool)*: True: the Port is operating, False: the Port is shutdown, default-value: True
  * **mode** *(str)*: One of the following vlan-modes: 0x00 (disabled), 0x01 (optional), 0x02 (enabled), 0x03 (strict); default-value is: 0x01
  * **receive** *(str)*: One of the following values, corresponding what kind of traffic the Port accepts: 0x00 (any), 0x01 (only tagged), 0x02 (only untagged); default-value is: 0x00
  * **force** *(bool)*: True: all ingress traffic is tagged with `default` VLAN, False: all ingress tags are kept; default-value: False
