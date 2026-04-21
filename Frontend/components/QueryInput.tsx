import React, { useState } from 'react';
import type { DataSet } from '../types';
import { QueryMode } from '../types';
import { IconPlay } from './icons/IconPlay';
import { IconSparkles } from './icons/IconSparkles';

interface QueryInputProps {
    dataset: DataSet;
    onRunQuery: (query: string, mode: QueryMode) => void;
    isLoading: boolean;
}

export const QueryInput: React.FC<QueryInputProps> = ({ dataset, onRunQuery, isLoading }) => {
    const [query, setQuery] = useState('');
    const [mode, setMode] = useState<QueryMode>(QueryMode.NL);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (query.trim() && !isLoading) {
            onRunQuery(query, mode);
        }
    };

    const placeholderText = mode === QueryMode.NL
        ? `Ask a question about "${dataset.name}", e.g., "What is the average monthly income for women in each state?"`
        : mode === QueryMode.SQL
            ? `Enter a SQL query for "${dataset.name}", e.g., "SELECT * FROM data LIMIT 10"`
            : `Enter a MongoDB query for "${dataset.name}", e.g., '[{"$group": {"_id": "$state", "avg_income": {"$avg": "$monthly_income"}}}]'`;


    return (
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-md mb-6 flex-shrink-0">
            <div className="flex items-center mb-3">
                <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-200 mr-4">
                    Query Editor
                </h2>
                <div className="flex items-center bg-gray-200 dark:bg-gray-700 rounded-full p-1">
                    <button
                        onClick={() => setMode(QueryMode.NL)}
                        className={`px-3 py-1 text-sm font-semibold rounded-full transition-colors ${
                            mode === QueryMode.NL ? 'bg-white dark:bg-gray-600 text-blue-600 dark:text-blue-300 shadow' : 'text-gray-600 dark:text-gray-300'
                        }`}
                    >
                        Natural Language
                    </button>
                    <button
                        onClick={() => setMode(QueryMode.SQL)}
                        className={`px-3 py-1 text-sm font-semibold rounded-full transition-colors ${
                            mode === QueryMode.SQL ? 'bg-white dark:bg-gray-600 text-blue-600 dark:text-blue-300 shadow' : 'text-gray-600 dark:text-gray-300'
                        }`}
                    >
                        SQL Query
                    </button>
                    <button
                        onClick={() => setMode(QueryMode.MongoDB)}
                        className={`px-3 py-1 text-sm font-semibold rounded-full transition-colors ${
                            mode === QueryMode.MongoDB ? 'bg-white dark:bg-gray-600 text-blue-600 dark:text-blue-300 shadow' : 'text-gray-600 dark:text-gray-300'
                        }`}
                    >
                        MongoDB Query
                    </button>
                </div>
            </div>
            <form onSubmit={handleSubmit} className="flex space-x-3">
                <textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder={placeholderText}
                    className="w-full h-24 p-2 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-gray-700 focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none"
                    disabled={isLoading}
                />
                <button
                    type="submit"
                    disabled={isLoading || !query.trim()}
                    className="flex items-center justify-center h-24 px-6 bg-green-500 text-white font-bold rounded-md hover:bg-green-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                    {isLoading ? (
                        <>
                          <IconSparkles className="h-5 w-5 mr-2 animate-pulse" />
                          Thinking...
                        </>
                    ) : (
                        <>
                          <IconPlay className="h-5 w-5 mr-2" />
                          Run Query
                        </>
                    )}
                </button>
            </form>
            <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                {mode === QueryMode.NL 
                    ? "Your question will be translated into a query." 
                    : mode === QueryMode.SQL
                        ? "Use simple SQL queries like 'SELECT * FROM data LIMIT 10'" 
                        : "Execute a raw MongoDB aggregation pipeline as JSON array."}
            </div>
        </div>
    );
};
