export interface ServiceAccount {
    username: string;
    domain: string;
    permissions: string[];
    last_login?: string;
}

export interface AuthResponse {
    access_token: string;
    token_type: string;
    expires_at: string;
    account: ServiceAccount;
}

export interface LoginCredentials {
    username: string;
    domain: string;
    password: string;
}

export interface AuthSession {
    valid: boolean;
    account: ServiceAccount;
    expires_at: string;
}

export interface AuthError {
    detail: string;
    status_code: number;
}