
import React, { useState, useCallback } from 'react';
import { IconUpload } from './icons/IconUpload';
import { IconX } from './icons/IconX';
import { Spinner } from './Spinner';

interface DataIngestionModalProps {
    onClose: () => void;
    onUpload: (file: File, name: string, description: string) => void;
    isLoading: boolean;
}

export const DataIngestionModal: React.FC<DataIngestionModalProps> = ({ onClose, onUpload, isLoading }) => {
    const [file, setFile] = useState<File | null>(null);
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [error, setError] = useState<string | null>(null);

    const ALLOWED_EXTS = ['.csv', '.pdf'];

    const validateAndSetFile = (f: File) => {
        const ext = '.' + f.name.split('.').pop()?.toLowerCase();
        if (!ALLOWED_EXTS.includes(ext)) {
            setError(`Unsupported file type "${ext}". Please upload a CSV or PDF file.`);
            setFile(null);
            return;
        }
        setError(null);
        setFile(f);
        if (!name) {
            setName(f.name.replace(/\.[^/.]+$/, ''));
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            validateAndSetFile(e.target.files[0]);
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!file || !name.trim() || !description.trim()) {
            setError('All fields are required.');
            return;
        }
        setError(null);
        onUpload(file, name, description);
    };

    const onDrop = useCallback((event: React.DragEvent<HTMLLabelElement>) => {
        event.preventDefault();
        event.stopPropagation();
        if (event.dataTransfer.files && event.dataTransfer.files[0]) {
            validateAndSetFile(event.dataTransfer.files[0]);
        }
    }, [name]);
    
    const onDragOver = (event: React.DragEvent<HTMLLabelElement>) => {
        event.preventDefault();
        event.stopPropagation();
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-8 w-full max-w-lg m-4 relative">
                <button onClick={onClose} className="absolute top-4 right-4 text-gray-500 hover:text-gray-800 dark:hover:text-gray-200">
                    <IconX className="h-6 w-6" />
                </button>
                <h2 className="text-2xl font-bold mb-6 text-gray-800 dark:text-white">Upload New Dataset</h2>
                <form onSubmit={handleSubmit} className="space-y-4">
                     <div>
                        <label htmlFor="dataset-name" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Dataset Name</label>
                        <input
                            type="text"
                            id="dataset-name"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            className="mt-1 block w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                            placeholder="e.g., National Family Health Survey 5"
                            required
                        />
                    </div>
                     <div>
                        <label htmlFor="dataset-description" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Description</label>
                        <textarea
                            id="dataset-description"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            rows={3}
                            className="mt-1 block w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                            placeholder="A brief description of the dataset"
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Dataset File</label>
                        <label
                           onDrop={onDrop}
                           onDragOver={onDragOver}
                           htmlFor="file-upload"
                           className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 dark:border-gray-600 border-dashed rounded-md cursor-pointer hover:border-blue-400 dark:hover:border-blue-500 bg-gray-50 dark:bg-gray-700/50"
                        >
                            <div className="space-y-1 text-center">
                                 <IconUpload className="mx-auto h-12 w-12 text-gray-400" />
                                 <div className="flex text-sm text-gray-600 dark:text-gray-400">
                                     <span className="relative rounded-md font-medium text-blue-600 dark:text-blue-400 hover:text-blue-500">
                                         <span>Upload a file</span>
                                     </span>
                                     <p className="pl-1">or drag and drop</p>
                                 </div>
                                 <p className="text-xs text-gray-500 dark:text-gray-500">CSV or PDF (with tables) up to 16MB</p>
                             </div>
                        </label>
                         <input id="file-upload" name="file-upload" type="file" accept=".csv,.pdf" className="sr-only" onChange={handleFileChange} />
                         {file && (
                              <div className="mt-2 flex items-center gap-2">
                                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold uppercase ${
                                      file.name.toLowerCase().endsWith('.pdf')
                                          ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'
                                          : 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300'
                                  }`}>
                                      {file.name.toLowerCase().endsWith('.pdf') ? 'PDF' : 'CSV'}
                                  </span>
                                  <p className="text-sm text-gray-500 dark:text-gray-400 truncate">{file.name}</p>
                              </div>
                          )}
                          {file?.name.toLowerCase().endsWith('.pdf') && (
                              <p className="mt-1 text-xs text-blue-600 dark:text-blue-400">
                                  📊 Tables will be automatically extracted from all pages of the PDF.
                              </p>
                          )}
                    </div>

                    {error && <p className="text-red-500 text-sm">{error}</p>}
                    
                    <div className="flex justify-end space-x-3 pt-4">
                        <button type="button" onClick={onClose} disabled={isLoading} className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 dark:bg-gray-600 dark:text-gray-200 dark:hover:bg-gray-500 disabled:opacity-50">
                            Cancel
                        </button>
                        <button type="submit" disabled={isLoading} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-blue-300 flex items-center">
                            {isLoading && <Spinner small={true} />}
                            {isLoading ? 'Uploading...' : 'Upload Dataset'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};
