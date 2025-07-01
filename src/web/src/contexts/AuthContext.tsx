import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '@/api/auth';
import type { ServiceAccount } from '@/types/auth';

interface AuthContextType {
    isAuthenticated: boolean;
    account: ServiceAccount | null;
    user: ServiceAccount | null; // Alias for account for compatibility
    login: (username: string, domain: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
    isLoading: boolean;
    error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
    const [account, setAccount] = useState<ServiceAccount | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const checkAuth = async () => {
            const token = localStorage.getItem('auth_token');
            if (token) {
                try {
                    const response = await authApi.verify();
                    setAccount(response.account);
                    setIsAuthenticated(true);
                } catch (err) {
                    localStorage.removeItem('auth_token');
                }
            }
            setIsLoading(false);
        };

        checkAuth();
    }, []);

    const login = async (username: string, domain: string, password: string) => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await authApi.login({ username, domain, password });
            localStorage.setItem('auth_token', response.access_token);
            setAccount(response.account);
            setIsAuthenticated(true);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Login failed');
            throw err;
        } finally {
            setIsLoading(false);
        }
    };

    const logout = async () => {
        setIsLoading(true);
        try {
            await authApi.logout();
        } catch (err) {
            console.error('Logout error:', err);
        } finally {
            localStorage.removeItem('auth_token');
            setIsAuthenticated(false);
            setAccount(null);
            setIsLoading(false);
        }
    };

    return (
        <AuthContext.Provider
            value={{
                isAuthenticated,
                account,
                user: account, // Alias for compatibility
                login,
                logout,
                isLoading,
                error,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}