
import React from 'react';
import { IconDatabase } from './icons/IconDatabase';

interface HeaderProps {
    user?: { name: string; email: string } | null;
    onLogout?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ user, onLogout }) => {
    return (
        <header className="bg-white dark:bg-gray-800 shadow-md p-4 flex items-center justify-between z-10 flex-shrink-0">
            <div className="flex items-center space-x-3">
                <IconDatabase className="h-8 w-8 text-blue-500" />
                <h1 className="text-xl font-bold text-gray-800 dark:text-white">
                    Query Mitra
                </h1>
            </div>
            <div className="flex items-center space-x-4">
                <div className="text-sm text-gray-500 dark:text-gray-400">
                    Query & Visualize Survey Microdata
                </div>
                {user && (
                    <div className="flex items-center space-x-3">
                        <div className="text-sm text-right">
                            <p className="font-medium text-gray-800 dark:text-white">{user.name}</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">{user.email}</p>
                        </div>
                        {onLogout && (
                            <button
                                onClick={onLogout}
                                className="px-3 py-1.5 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
                            >
                                Logout
                            </button>
                        )}
                    </div>
                )}
            </div>
        </header>
    );
};
