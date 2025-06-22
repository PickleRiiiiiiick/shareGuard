import axios from 'axios';
import { API_CONFIG } from '@/config/api';

const createApiInstance = (basePath: string = '') => {
    const instance = axios.create({
        headers: {
            'Content-Type': 'application/json',
        },
    });

    // Add request interceptor for authentication
    instance.interceptors.request.use((config) => {
        // Remove the duplicate /api/v1 prefix since it's already in FastAPI
        config.url = `${basePath}${config.url || ''}`;

        const token = localStorage.getItem('auth_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        // Debug log
        console.log('Making API request:', {
            fullUrl: config.url,
            method: config.method,
            headers: config.headers,
            data: config.data ? { ...config.data, password: '[REDACTED]' } : undefined
        });

        return config;
    });

    instance.interceptors.response.use(
        (response) => {
            console.log('API response success:', {
                status: response.status,
                headers: response.headers,
                data: response.data
            });
            return response.data;
        },
        (error) => {
            console.error('API response error:', {
                status: error.response?.status,
                statusText: error.response?.statusText,
                data: error.response?.data,
                headers: error.response?.headers,
                config: {
                    url: error.config?.url,
                    method: error.config?.method,
                    headers: error.config?.headers
                }
            });
            throw error;
        }
    );

    return instance;
};

// Create API instances for different endpoints with correct prefixes
export const api = {
    auth: createApiInstance('/api/v1/auth'),
    scan: createApiInstance('/api/v1/scan'),
    targets: createApiInstance('/api/v1/targets'),
    folders: createApiInstance('/api/v1/folders')
};