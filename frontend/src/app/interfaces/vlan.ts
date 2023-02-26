export interface Vlan {
    id: string;
    number: number;
    purpose: VlanPurposeType;
    desc: string;
}

export enum VlanPurposeType {
    play,
    mgmt,
    onboarding,
    other
}
