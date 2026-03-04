
import React from 'react';
import { IconDatabase } from './icons/IconDatabase';

interface HeaderProps {
    user?: { name: string; email: string } | null;
    onLogout?: () => void;
    activeView?: 'query' | 'library';
    onViewChange?: (view: 'query' | 'library') => void;
}

export const Header: React.FC<HeaderProps> = ({ user, onLogout, activeView, onViewChange }) => {
    return (
        <header className="bg-white dark:bg-gray-800 shadow-md z-10 flex-shrink-0">
            <div className="px-4 py-3 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                    <IconDatabase className="h-8 w-8 text-blue-500" />
                    <h1 className="text-xl font-bold text-gray-800 dark:text-white">
                        Query Mitra
                    </h1>
                </div>

                {/* Nav tabs — only shown when view switching is available */}
                {onViewChange && (
                    <nav className="flex items-center gap-1 bg-gray-100 dark:bg-gray-700 p-1 rounded-lg">
                        <button
                            onClick={() => onViewChange('query')}
                            className={`flex items-center gap-1.5 px-4 py-1.5 rounded-md text-sm font-medium transition-all ${
                                activeView === 'query'
                                    ? 'bg-white dark:bg-gray-900 text-blue-600 dark:text-blue-400 shadow-sm'
                                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
                            }`}
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                            </svg>
                            Query
                        </button>
                        <button
                            onClick={() => onViewChange('library')}
                            className={`flex items-center gap-1.5 px-4 py-1.5 rounded-md text-sm font-medium transition-all ${
                                activeView === 'library'
                                    ? 'bg-white dark:bg-gray-900 text-blue-600 dark:text-blue-400 shadow-sm'
                                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
                            }`}
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z"/>
                            </svg>
                            CSV Library
                        </button>
                    </nav>
                )}

                <div className="flex items-center space-x-4">
                    <div className="text-sm text-gray-500 dark:text-gray-400 hidden sm:block">
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
            </div>
        </header>
    );
};
