// src/web/src/App.tsx
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import { LoginForm } from '@/components/auth/LoginForm';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { Dashboard } from '@/pages/Dashboard';
import { ScanTargetList } from '@/components/scanning/ScanTargetList';
import { PermissionsPage } from '@/pages/Permissions';

export default function App() {
    return (
        <AuthProvider>
            <Routes>
                {/* Public routes */}
                <Route path="/login" element={<LoginForm />} />

                {/* Protected routes */}
                <Route element={<ProtectedRoute />}>
                    <Route element={<DashboardLayout />}>
                        {/* Dashboard routes */}
                        <Route path="/" element={<Navigate to="/dashboard" replace />} />
                        <Route path="/dashboard" element={<Dashboard />} />
                        <Route path="/targets" element={<ScanTargetList />} />
                        <Route path="/scans" element={<Dashboard />} />
                        <Route path="/permissions" element={<PermissionsPage />} />
                        <Route path="/settings" element={<Dashboard />} />
                    </Route>
                </Route>

                {/* Catch-all route */}
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
        </AuthProvider>
    );
}