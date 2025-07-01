import { useLocation, Link } from 'react-router-dom';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import {
    XMarkIcon,
    HomeIcon,
    FolderIcon,
    ShieldCheckIcon,
    CogIcon,
    ClockIcon,
    BellIcon,
    ChartBarIcon,
} from '@heroicons/react/24/outline';

interface SidebarProps {
    isOpen: boolean;
    onClose: () => void;
}

const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
    { name: 'Scan Targets', href: '/targets', icon: FolderIcon },
    { name: 'Scan History', href: '/scans', icon: ClockIcon },
    { name: 'Permissions', href: '/permissions', icon: ShieldCheckIcon },
    { name: 'Health', href: '/health', icon: ChartBarIcon },
    { name: 'Alerts', href: '/alerts', icon: BellIcon },
    { name: 'Settings', href: '/settings', icon: CogIcon },
];

export function Sidebar({ isOpen, onClose }: SidebarProps) {
    const location = useLocation();

    return (
        <>
            {/* Mobile sidebar */}
            <Transition.Root show={isOpen} as={Fragment}>
                <Dialog as="div" className="relative z-50 lg:hidden" onClose={onClose}>
                    <Transition.Child
                        as={Fragment}
                        enter="transition-opacity ease-linear duration-300"
                        enterFrom="opacity-0"
                        enterTo="opacity-100"
                        leave="transition-opacity ease-linear duration-300"
                        leaveFrom="opacity-100"
                        leaveTo="opacity-0"
                    >
                        <div className="fixed inset-0 bg-gray-900/80" />
                    </Transition.Child>

                    <div className="fixed inset-0 flex">
                        <Transition.Child
                            as={Fragment}
                            enter="transition ease-in-out duration-300 transform"
                            enterFrom="-translate-x-full"
                            enterTo="translate-x-0"
                            leave="transition ease-in-out duration-300 transform"
                            leaveFrom="translate-x-0"
                            leaveTo="-translate-x-full"
                        >
                            <Dialog.Panel className="relative mr-16 flex w-full max-w-xs flex-1">
                                <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-white px-6 pb-4">
                                    <div className="flex h-16 shrink-0 items-center">
                                        <button
                                            onClick={onClose}
                                            className="absolute right-4 top-4 text-gray-400 hover:text-gray-500"
                                        >
                                            <XMarkIcon className="h-6 w-6" />
                                        </button>
                                    </div>
                                    <nav className="flex flex-1 flex-col">
                                        <ul role="list" className="flex flex-1 flex-col gap-y-7">
                                            {navigation.map((item) => (
                                                <li key={item.name}>
                                                    <Link
                                                        to={item.href}
                                                        className={`group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold ${location.pathname === item.href
                                                                ? 'bg-gray-50 text-primary-600'
                                                                : 'text-gray-700 hover:text-primary-600 hover:bg-gray-50'
                                                            }`}
                                                        onClick={onClose}
                                                    >
                                                        <item.icon
                                                            className={`h-6 w-6 shrink-0 ${location.pathname === item.href
                                                                    ? 'text-primary-600'
                                                                    : 'text-gray-400 group-hover:text-primary-600'
                                                                }`}
                                                        />
                                                        {item.name}
                                                    </Link>
                                                </li>
                                            ))}
                                        </ul>
                                    </nav>
                                </div>
                            </Dialog.Panel>
                        </Transition.Child>
                    </div>
                </Dialog>
            </Transition.Root>

            {/* Desktop sidebar */}
            <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-64 lg:flex-col">
                <div className="flex grow flex-col gap-y-5 overflow-y-auto border-r border-gray-200 bg-white px-6 pb-4">
                    <div className="flex h-16 shrink-0 items-center">
                        {/* Logo */}
                        <span className="text-2xl font-bold text-primary-600">
                            ShareGuard
                        </span>
                    </div>
                    <nav className="flex flex-1 flex-col">
                        <ul role="list" className="flex flex-1 flex-col gap-y-7">
                            {navigation.map((item) => (
                                <li key={item.name}>
                                    <Link
                                        to={item.href}
                                        className={`group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold ${location.pathname === item.href
                                                ? 'bg-gray-50 text-primary-600'
                                                : 'text-gray-700 hover:text-primary-600 hover:bg-gray-50'
                                            }`}
                                    >
                                        <item.icon
                                            className={`h-6 w-6 shrink-0 ${location.pathname === item.href
                                                    ? 'text-primary-600'
                                                    : 'text-gray-400 group-hover:text-primary-600'
                                                }`}
                                        />
                                        {item.name}
                                    </Link>
                                </li>
                            ))}
                        </ul>
                    </nav>
                </div>
            </div>
        </>
    );
}