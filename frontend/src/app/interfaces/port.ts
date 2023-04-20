export interface Port {
    id: string;
    number: number;
    desc: string;
    switch_id: string;
    participants: boolean;
    vlan_ids: string[];
    type: string;
    enabled: boolean;
    link: boolean;
    speed: string;
}
