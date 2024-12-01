// API Response types
export interface ApiAuthResponse {
    access_token: string;
    token_type: string;
    expires_at: string;
    account: {
        username: string;
        domain: string;
        permissions: string[];
    };
}