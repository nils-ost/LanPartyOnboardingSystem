# element save/create error-codes

## generic

  * **1**: marked as not to be None
  * **2**: marked as unique, but element with value <value\> allready present
  * **3**: needs to be of type <type\> [or None]

## vlan

  * **10***(number)*: needs to be a value from 1 to 1024
  * **11***(purpose)*: needs to be 0, 1, 2 or 3
  * **12***(purpose)*: values 0 and 1 need to be unique, but element with value <value\> allready present

# element delete error-codes

  * **1**: at least one IpPool is using this <element_type\>
  * **2**: at least one Table is using this <element_type\>
  * **3**: at least one Seat is uning this <element_type\>
