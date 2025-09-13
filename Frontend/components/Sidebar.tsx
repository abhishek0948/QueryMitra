
import React from 'react';
import type { DataSet } from '../types';
import { IconUpload } from './icons/IconUpload';
import { IconDatabase } from './icons/IconDatabase';

interface SidebarProps {
    datasets: DataSet[];
    selectedDatasetId: string | null | undefined;
    onSelectDataset: (id: string) => void;
    onUploadClick: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ datasets, selectedDatasetId, onSelectDataset, onUploadClick }) => {
    return (
        <aside className="w-80 bg-white dark:bg-gray-800 p-4 flex flex-col border-r border-gray-200 dark:border-gray-700 flex-shrink-0">
            <div className="mb-4">
                <button
                    onClick={onUploadClick}
                    className="w-full flex items-center justify-center bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-lg transition-colors duration-200"
                >
                    <IconUpload className="h-5 w-5 mr-2" />
                    Upload New Dataset
                </button>
            </div>
            <h2 className="text-lg font-semibold mb-2 text-gray-700 dark:text-gray-300">Available Datasets</h2>
            <div className="flex-1 overflow-y-auto">
                <ul className="space-y-2">
                    {datasets.map((dataset) => (
                        <li key={dataset.id}>
                            <button
                                onClick={() => onSelectDataset(dataset.id)}
                                className={`w-full text-left p-3 rounded-lg transition-colors duration-200 ${
                                    selectedDatasetId === dataset.id
                                        ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200'
                                        : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300'
                                }`}
                            >
                                <div className="flex items-start space-x-3">
                                    <IconDatabase className="h-5 w-5 mt-1 text-gray-400 flex-shrink-0" />
                                    <div>
                                        <p className="font-semibold">{dataset.name}</p>
                                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{dataset.description}</p>
                                    </div>
                                </div>
                            </button>
                        </li>
                    ))}
                </ul>
            </div>
        </aside>
    );
};
