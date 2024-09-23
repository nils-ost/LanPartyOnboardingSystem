export interface PortCommitConfig {
    vlans: string[];
    default: string;
    enabled: boolean;
    mode: string;
    receive: string;
    force: boolean;
}

export interface PortConfigCache {
    id: string | undefined;
    port_id: string | undefined;
    scope: number | undefined;
    isolate: boolean;
    vlan_ids: string[];
    default_vlan_id: string | null;
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
    retreat_disabled: boolean;
    commit_config: any | null;
    retreat_config: any | null;
    vlan_ids: string[];
    default_vlan_id: string | null;
    type: string;
    enabled: boolean;
    link: boolean;
    speed: string;
    receive: string;
    calculated_commit_config: PortConfigCache;
    calculated_retreat_config: PortConfigCache;
}
