import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import { AlertProvider } from '@/contexts/AlertContext';
import { LoginForm } from '@/components/auth/LoginForm';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { ScanTargetList } from '@/components/scanning/ScanTargetList';
import { DashboardPage } from '@/components/dashboard/DashboardPage';
import { PermissionsPage } from '@/pages/Permissions';
import Alerts from '@/pages/Alerts';
import { Health } from '@/pages/Health';


export default function App() {
    return (
        <AuthProvider>
            <AlertProvider>
                <Routes>
                    {/* Public routes */}
                    <Route path="/login" element={<LoginForm />} />

                    {/* Protected routes */}
                    <Route element={<ProtectedRoute />}>
                        <Route element={<DashboardLayout />}>
                            {/* Dashboard routes will be nested here */}
                            <Route path="/" element={<Navigate to="/dashboard" replace />} />
                            <Route path="/dashboard" element={<DashboardPage />} />
                            <Route path="/targets" element={<ScanTargetList />} />
                            <Route path="/permissions" element={<PermissionsPage />} />
                            <Route path="/health" element={<Health />} />
                            <Route path="/alerts" element={<Alerts />} />
                        </Route>
                    </Route>

                    {/* Catch-all route */}
                    <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Routes>
            </AlertProvider>
        </AuthProvider>
    );
}