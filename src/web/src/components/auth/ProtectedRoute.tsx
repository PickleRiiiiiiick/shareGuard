import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { LoadingSpinner } from '@components/common/LoadingSpinner';

export function ProtectedRoute() {
    const { isAuthenticated, isLoading, account } = useAuth();
    const location = useLocation();

    if (isLoading) {
        return (
            <div className="h-screen w-screen flex items-center justify-center">
                <LoadingSpinner size="lg" />
            </div>
        );
    }

    if (!isAuthenticated || !account) {
        // Redirect to login but save the attempted url
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    return <Outlet />;
}