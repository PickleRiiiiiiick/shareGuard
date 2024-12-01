import { Fragment } from 'react';
import { useNavigate } from 'react-router-dom';
import { Menu, Transition } from '@headlessui/react';
import { useAuth } from '@contexts/AuthContext';
import {
    Bars3Icon,
    BellIcon,
    UserCircleIcon,
} from '@heroicons/react/24/outline';

interface NavbarProps {
    onMenuClick: () => void;
}

export function Navbar({ onMenuClick }: NavbarProps) {
    const { account, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    return (
        <nav className="fixed top-0 z-50 w-full bg-white border-b border-gray-200 lg:pl-64">
            <div className="px-4 py-2.5 lg:px-5 lg:pl-3">
                <div className="flex items-center justify-between">
                    <div className="flex items-center">
                        <button
                            onClick={onMenuClick}
                            className="inline-flex items-center p-2 text-sm text-gray-500 rounded-lg lg:hidden hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-200"
                        >
                            <Bars3Icon className="w-6 h-6" />
                        </button>
                        <span className="self-center text-xl font-semibold sm:text-2xl whitespace-nowrap text-primary-600">
                            ShareGuard
                        </span>
                    </div>

                    <div className="flex items-center gap-3">
                        <button className="p-2 text-gray-500 rounded-lg hover:bg-gray-100">
                            <BellIcon className="w-6 h-6" />
                        </button>

                        <Menu as="div" className="relative">
                            <Menu.Button className="flex text-sm bg-gray-800 rounded-full focus:ring-4 focus:ring-gray-300">
                                <UserCircleIcon className="w-8 h-8 text-gray-400" />
                            </Menu.Button>

                            <Transition
                                as={Fragment}
                                enter="transition ease-out duration-100"
                                enterFrom="transform opacity-0 scale-95"
                                enterTo="transform opacity-100 scale-100"
                                leave="transition ease-in duration-75"
                                leaveFrom="transform opacity-100 scale-100"
                                leaveTo="transform opacity-0 scale-95"
                            >
                                <Menu.Items className="absolute right-0 z-10 mt-2 w-48 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                                    <Menu.Item>
                                        {() => (
                                            <div className="px-4 py-2 text-sm text-gray-700">
                                                {account?.username}
                                            </div>
                                        )}
                                    </Menu.Item>
                                    <Menu.Item>
                                        {({ active }) => (
                                            <a
                                                href="#"
                                                className={`block px-4 py-2 text-sm ${active ? 'bg-gray-100' : ''
                                                    } text-gray-700`}
                                                onClick={(e) => {
                                                    e.preventDefault();
                                                    navigate('/settings');
                                                }}
                                            >
                                                Settings
                                            </a>
                                        )}
                                    </Menu.Item>
                                    <Menu.Item>
                                        {({ active }) => (
                                            <a
                                                href="#"
                                                className={`block px-4 py-2 text-sm ${active ? 'bg-gray-100' : ''
                                                    } text-gray-700`}
                                                onClick={(e) => {
                                                    e.preventDefault();
                                                    handleLogout();
                                                }}
                                            >
                                                Logout
                                            </a>
                                        )}
                                    </Menu.Item>
                                </Menu.Items>
                            </Transition>
                        </Menu>
                    </div>
                </div>
            </div>
        </nav>
    );
}
