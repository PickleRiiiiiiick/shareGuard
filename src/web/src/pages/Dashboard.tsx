import { ScanStatusWidget } from '@components/dashboard/ScanStatusWidget';
import { RecentScansTable } from '@components/dashboard/RecentScansTable';
import { useAuth } from '@/contexts/AuthContext';

export function Dashboard() {
    const { account } = useAuth();

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
                <p className="mt-1 text-sm text-gray-500">
                    Welcome back, {account?.username}
                </p>
            </div>

            <div className="grid grid-cols-1 gap-6">
                <ScanStatusWidget />
                <RecentScansTable />
            </div>
        </div>
    );
}