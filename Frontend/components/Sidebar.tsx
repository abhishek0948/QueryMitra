
import React, { useState } from 'react';
import type { DataSet } from '../types';
import { IconUpload } from './icons/IconUpload';
import { IconDatabase } from './icons/IconDatabase';

interface SidebarProps {
    datasets: DataSet[];
    selectedDatasetId: string | null | undefined;
    onSelectDataset: (id: string) => void;
    onUploadClick: () => void;
    onDeleteDataset: (id: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ datasets, selectedDatasetId, onSelectDataset, onUploadClick, onDeleteDataset }) => {
    const [expandedDatasetId, setExpandedDatasetId] = useState<string | null>(null);
    const [deletingId, setDeletingId] = useState<string | null>(null);

    const toggleExpand = (datasetId: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setExpandedDatasetId(expandedDatasetId === datasetId ? null : datasetId);
    };

    const handleDelete = async (datasetId: string, e: React.MouseEvent) => {
        e.stopPropagation();
        if (window.confirm('Are you sure you want to delete this dataset? This action cannot be undone.')) {
            setDeletingId(datasetId);
            try {
                await onDeleteDataset(datasetId);
            } finally {
                setDeletingId(null);
            }
        }
    };

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
                    {datasets.map((dataset) => {
                        const isExpanded = expandedDatasetId === dataset.id;
                        const columnCount = Object.keys(dataset.schema || {}).length;
                        
                        return (
                            <li key={dataset.id} className="border border-gray-200 dark:border-gray-700 rounded-lg">
                                <button
                                    onClick={() => onSelectDataset(dataset.id)}
                                    className={`w-full text-left p-3 rounded-lg transition-colors duration-200 ${
                                        selectedDatasetId === dataset.id
                                            ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200'
                                            : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300'
                                    }`}
                                >
                                    <div className="flex items-start justify-between">
                                        <div className="flex items-start space-x-3 flex-1">
                                            <IconDatabase className="h-5 w-5 mt-1 text-gray-400 flex-shrink-0" />
                                            <div className="flex-1 min-w-0">
                                                <p className="font-semibold truncate">{dataset.name}</p>
                                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">{dataset.description}</p>
                                                <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                                                    {columnCount} column{columnCount !== 1 ? 's' : ''}
                                                </p>
                                            </div>
                                        </div>
                                        <div className="flex items-center space-x-1 ml-2">
                                            <button
                                                onClick={(e) => handleDelete(dataset.id, e)}
                                                disabled={deletingId === dataset.id}
                                                className="p-1 hover:bg-red-100 dark:hover:bg-red-900/30 rounded transition-colors group"
                                                title="Delete dataset"
                                            >
                                                {deletingId === dataset.id ? (
                                                    <svg className="w-4 h-4 animate-spin text-red-500" fill="none" viewBox="0 0 24 24">
                                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                    </svg>
                                                ) : (
                                                    <svg className="w-4 h-4 text-gray-400 group-hover:text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                    </svg>
                                                )}
                                            </button>
                                            <button
                                                onClick={(e) => toggleExpand(dataset.id, e)}
                                                className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors"
                                                title={isExpanded ? "Hide columns" : "Show columns"}
                                            >
                                                <svg
                                                    className={`w-4 h-4 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
                                                    fill="none"
                                                    stroke="currentColor"
                                                    viewBox="0 0 24 24"
                                                >
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                                </svg>
                                            </button>
                                        </div>
                                    </div>
                                </button>
                                
                                {isExpanded && dataset.schema && (
                                    <div className="px-3 pb-3 pt-2 bg-gray-50 dark:bg-gray-900/50 rounded-b-lg">
                                        <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2 uppercase tracking-wide">
                                            Column Names:
                                        </p>
                                        <div className="space-y-1 max-h-60 overflow-y-auto">
                                            {Object.entries(dataset.schema).map(([columnName, columnType]) => (
                                                <div
                                                    key={columnName}
                                                    className="flex items-center justify-between text-xs py-1.5 px-2 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700"
                                                >
                                                    <span className="font-mono text-gray-800 dark:text-gray-200 truncate flex-1">
                                                        {columnName}
                                                    </span>
                                                    <span className={`ml-2 px-2 py-0.5 rounded text-xs font-medium flex-shrink-0 ${
                                                        columnType === 'number' 
                                                            ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300'
                                                            : columnType === 'boolean'
                                                            ? 'bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-300'
                                                            : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                                                    }`}>
                                                        {columnType}
                                                    </span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </li>
                        );
                    })}
                </ul>
            </div>
        </aside>
    );
};
