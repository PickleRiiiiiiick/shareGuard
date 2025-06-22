// src/components/dashboard/DashboardPage.tsx

export function DashboardPage() {
    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-bold text-gray-900">Welcome to ShareGuard</h1>
            <p className="text-gray-700">
                This dashboard gives you an overview of your scan activity, permissions, and recent events.
            </p>
            {/* Later: insert widgets, stats, etc. */}
        </div>
    );
}
