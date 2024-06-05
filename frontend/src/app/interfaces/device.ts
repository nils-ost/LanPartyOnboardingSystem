export interface Device {
    id: string;
    mac: string;
    desc: string;
    seat_id: string | null;
    participant_id: string | null;
    ip_pool_id: string | null;
    ip: number | null;
    port_id: string | null;
    onboarding_blocked: boolean;
    pw_strikes: number;
    last_scan_ts: number;
}
