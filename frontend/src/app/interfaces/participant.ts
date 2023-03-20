export interface Participant {
    id: string;
    admin: boolean;
    name: string;
    login: string | null;
    pw: string | null;
    seat_id: string | null;
}
