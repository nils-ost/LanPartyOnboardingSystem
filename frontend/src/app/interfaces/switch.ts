export interface Switch {
    id: string;
    desc: string;
    addr: string;
    user: string;
    pw: string;
    purpose: SwitchPurposeType;
    commited: boolean;
    onboarding_vlan_id: string| null;
    connected: boolean;
    mac: string;
    known_vlans: string[];
    port_numbering_offset: number;
}

export enum SwitchPurposeType {
    core,
    participants,
    mixed
}
