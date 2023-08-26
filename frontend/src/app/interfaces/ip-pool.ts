export interface IpPool {
    id: string;
    desc: string;
    mask: number;
    range_start: number;
    range_end: number;
    lpos: boolean;
    vlan_id: string;
}
