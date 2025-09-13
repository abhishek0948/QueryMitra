import React from 'react';
import { IconDatabase } from './icons/IconDatabase';
import { IconUpload } from './icons/IconUpload';

interface WelcomeScreenProps {
    onUploadClick: () => void;
}

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onUploadClick }) => {
    return (
        <div className="flex flex-col items-center justify-center h-full text-center bg-white dark:bg-gray-800 rounded-lg p-8">
            <IconDatabase className="h-24 w-24 text-blue-200 dark:text-blue-800 mb-4" />
            <h2 className="text-2xl font-bold text-gray-800 dark:text-white mb-2">Welcome to the Query Mitra</h2>
            <p className="text-gray-600 dark:text-gray-300 max-w-md mb-6">
                Please select a dataset from the sidebar on the left to begin querying, or upload your own dataset to start your analysis.
            </p>
            <button
                onClick={onUploadClick}
                className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-lg transition-colors duration-200 flex items-center"
            >
                <IconUpload className="h-5 w-5 mr-2" />
                Upload a Dataset
            </button>
        </div>
    );
};
