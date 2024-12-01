import { useState } from 'react';
import { ApiAuthResponse } from '@/types/api';
import axios from 'axios';

export function useAuth() {
    const [error, setError] = useState<string | null>(null);

    const login = async (username: string, domain: string, password: string) => {
        try {
            setError(null);

            const response = await axios.post<ApiAuthResponse>(
                '/api/v1/auth/login',
                {
                    username,
                    domain,
                    password
                },
                {
                    headers: {
                        'Content-Type': 'application/json'
                    }
                }
            );

            if (response.data.access_token) {
                localStorage.setItem('auth_token', response.data.access_token);
                localStorage.setItem('user', JSON.stringify(response.data.account));
                return response.data;
            }

            throw new Error('Invalid response from server');
        } catch (err: any) {
            console.error('Login error:', {
                status: err.response?.status,
                data: err.response?.data,
            });

            setError(err.response?.data?.detail || 'Failed to login. Please try again.');
            throw err;
        }
    };

    const logout = async () => {
        try {
            const token = localStorage.getItem('auth_token');
            if (token) {
                await axios.post('/api/v1/auth/logout', {}, {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                });
            }
        } finally {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user');
        }
    };

    return {
        login,
        logout,
        error
    };
}