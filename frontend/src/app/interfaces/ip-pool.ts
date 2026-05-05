export interface IpPool {
    id: string;
    desc: string;
    mask: number;
    range_start: number;
    range_end: number;
    vlan_id: string;
}
