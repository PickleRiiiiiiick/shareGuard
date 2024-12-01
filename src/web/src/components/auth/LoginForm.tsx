import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

export function LoginForm() {
    const [username, setUsername] = useState('');
    const [domain, setDomain] = useState('');
    const [password, setPassword] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [loginError, setLoginError] = useState('');
    const { login, error } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);
        setLoginError('');

        try {
            // Remove any extra escaping from the password
            const cleanPassword = password.replace(/\\\\/g, '\\');

            const result = await login(username, domain, cleanPassword);
            console.log('Login successful:', result);
            navigate('/dashboard');
        } catch (err: any) {
            console.error('Login error details:', {
                status: err.status,
                message: err.message,
                details: err.details
            });

            setLoginError(
                err.response?.data?.detail ||
                err.message ||
                'Failed to login. Please try again.'
            );
        } finally {
            setIsSubmitting(false);
        }
    };

    // Only show the latest error message (either from context or local state)
    const displayError = loginError || error;

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-lg">
                <div>
                    <h2 className="text-center text-3xl font-extrabold text-gray-900">
                        ShareGuard Login
                    </h2>
                </div>
                <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                    <div className="rounded-md shadow-sm space-y-4">
                        <div>
                            <label htmlFor="domain" className="block text-sm font-medium text-gray-700">
                                Domain
                            </label>
                            <input
                                id="domain"
                                type="text"
                                required
                                className="appearance-none rounded relative block w-full px-3 py-2 border border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                value={domain}
                                onChange={(e) => setDomain(e.target.value)}
                                disabled={isSubmitting}
                            />
                        </div>
                        <div>
                            <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                                Username
                            </label>
                            <input
                                id="username"
                                type="text"
                                required
                                className="appearance-none rounded relative block w-full px-3 py-2 border border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                disabled={isSubmitting}
                            />
                        </div>
                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                                Password
                            </label>
                            <input
                                id="password"
                                type="password"
                                required
                                className="appearance-none rounded relative block w-full px-3 py-2 border border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                disabled={isSubmitting}
                            />
                        </div>
                    </div>

                    {displayError && (
                        <div className="text-red-600 text-sm text-center bg-red-50 p-2 rounded">
                            {displayError}
                        </div>
                    )}

                    <div>
                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                        >
                            {isSubmitting ? 'Signing in...' : 'Sign in'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}