# Detailed information about Element-Attributes

## Port.commit_disabled

Boolean - default value is False

If set to True this Port is not touched during commits, if it is False configuration is done according to `Port.commit_config`

## Port.commit_config

This attribute can be None or dict()

If it is None, this means the Port is configured automatically, if it is a dict() the config contained in the dict() is written to port on commit.

### possible attributes in dict()

  * **vlans** *(list(str))*: list of VlanIds this Port has access to. Must contain at least one VlanId
  * **default** *(str)*: defines the VLAN(tag) that is given to untagged traffic on this port. If it is not explicitly set, the first entry of vlans is assigned
  * **enabled** *(bool)*: True: the Port is operating, False: the Port is shutdown, default-value: True
  * **mode** *(str)*: One of the following vlan-modes: disabled, optional, enabled, strict; default-value is: optional
  * **receive** *(str)*: One of the following values, corresponding what kind of traffic the Port accepts: any, only tagged, only untagged; default-value is: any
  * **force** *(bool)*: True: all ingress traffic is tagged with `default` VLAN, False: all ingress tags are kept; default-value: False

## Port.retreat_disabled

Boolean - default value is False

If set to True this Port is not touched during retreats, if it is False configuration is done according to `Port.retreat_config`

## Port.retreat_config

This attribute can be None or dict()

If it is None, this means the Port is configured automatically, if it is a dict() the config contained in the dict() is written to port on retreat.

### possible attributes in dict()

*same as for `Port.commit_config`*
