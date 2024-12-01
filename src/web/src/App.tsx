import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import { LoginForm } from '@/components/auth/LoginForm';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
//import { LoadingSpinner } from '@/components/common/LoadingSpinner';

export default function App() {
    return (
        <AuthProvider>
            <Routes>
                {/* Public routes */}
                <Route path="/login" element={<LoginForm />} />

                {/* Protected routes */}
                <Route element={<ProtectedRoute />}>
                    <Route element={<DashboardLayout />}>
                        {/* Dashboard routes will be nested here */}
                        <Route path="/" element={<Navigate to="/dashboard" replace />} />
                        <Route path="/dashboard" element={<div>Dashboard Content</div>} />
                        <Route path="/targets" element={<div>Scan Targets</div>} />
                        <Route path="/scans" element={<div>Scan History</div>} />
                        <Route path="/permissions" element={<div>Permissions</div>} />
                        <Route path="/settings" element={<div>Settings</div>} />
                    </Route>
                </Route>

                {/* Catch-all route */}
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
        </AuthProvider>
    );
}