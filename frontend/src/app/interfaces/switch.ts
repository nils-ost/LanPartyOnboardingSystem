export interface Switch {
    id: string;
    addr: string;
    user: string;
    pw: string;
    purpose: SwitchPurposeType;
    onboarding_vlan_id: string| null;
}

export enum SwitchPurposeType {
    core,
    participants,
    mixed
}
