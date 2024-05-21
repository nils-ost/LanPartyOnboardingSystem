export interface PortCommitConfig {
    vlans: string[];
    default: string;
    enabled: boolean;
    mode: string;
    receive: string;
    force: boolean;
}

export interface Port {
    id: string;
    number: number;
    desc: string;
    switch_id: string;
    participants: boolean;
    switchlink: boolean;
    switchlink_port_id: string | null;
    commit_disabled: boolean;
    commit_config: PortCommitConfig | null;
    vlan_ids: string[];
    type: string;
    enabled: boolean;
    link: boolean;
    speed: string;
}
