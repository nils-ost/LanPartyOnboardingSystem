export interface Port {
    id: string;
    number: number;
    desc: string;
    switch_id: string;
    participants: boolean;
    switchlink: boolean;
    switchlink_port_id: string | null;
    commit_disabled: boolean;
    vlan_ids: string[];
    type: string;
    enabled: boolean;
    link: boolean;
    speed: string;
}
