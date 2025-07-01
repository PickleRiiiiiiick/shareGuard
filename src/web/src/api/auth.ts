import axios from 'axios';
import { API_CONFIG } from '@/config/api';
import type { LoginCredentials, AuthResponse, AuthSession } from '@/types/auth';

const api = axios.create({
    baseURL: '/api/v1/auth',
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true
});

// Add auth token to requests if it exists
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }

    // Debug log
    console.log('Making request:', {
        url: config.url,
        fullUrl: `${config.baseURL}${config.url}`,
        method: config.method,
        headers: config.headers,
    });

    return config;
});

export const authApi = {
    login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
        try {
            console.log('Attempting login with:', {
                ...credentials,
                password: '[REDACTED]',
            });
            const response = await api.post<AuthResponse>('/login', credentials);
            return response.data;
        } catch (error: any) {
            console.error('Login failed:', {
                status: error.response?.status,
                data: error.response?.data,
            });
            throw error;
        }
    },

    logout: async (): Promise<void> => {
        await api.post('/logout');
    },

    verify: async (): Promise<AuthSession> => {
        const response = await api.get<AuthSession>('/verify');
        return response.data;
    },
};
