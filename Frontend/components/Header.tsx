
import React from 'react';
import { IconDatabase } from './icons/IconDatabase';

export const Header: React.FC = () => {
    return (
        <header className="bg-white dark:bg-gray-800 shadow-md p-4 flex items-center justify-between z-10 flex-shrink-0">
            <div className="flex items-center space-x-3">
                <IconDatabase className="h-8 w-8 text-blue-500" />
                <h1 className="text-xl font-bold text-gray-800 dark:text-white">
                    Query Mitra
                </h1>
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
                Query & Visualize Survey Microdata
            </div>
        </header>
    );
};
