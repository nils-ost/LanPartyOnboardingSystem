export interface Device {
    id: string;
    mac: string;
    desc: string;
    seat_id: string | null;
    participant_id: string | null;
    ip_pool_id: string | null;
    ip: number | null;
}
