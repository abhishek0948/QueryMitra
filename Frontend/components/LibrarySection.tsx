import React, { useState, useEffect, useCallback } from 'react';
import { getLibraryFiles, previewLibraryFile, importLibraryFile } from '../services/apiService';
import { Spinner } from './Spinner';

interface LibraryFile {
    fileName: string;
    rowCount: number;
    uploadedAt: string;
    tag: 'User' | 'Admin';
}

interface PreviewData {
    columns: string[];
    rows: any[];
}

interface LibrarySectionProps {
    /** When true the viewer is an admin and can access Admin-tagged files */
    isAdmin?: boolean;
    /** Called after a successful import so the parent can refresh datasets */
    onImportSuccess?: (newDatasetName: string) => void;
}

export const LibrarySection: React.FC<LibrarySectionProps> = ({ isAdmin = false, onImportSuccess }) => {
    const [files, setFiles] = useState<LibraryFile[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Preview modal
    const [previewFile, setPreviewFile] = useState<LibraryFile | null>(null);
    const [previewData, setPreviewData] = useState<PreviewData | null>(null);
    const [previewLoading, setPreviewLoading] = useState(false);
    const [previewError, setPreviewError] = useState<string | null>(null);

    // Import state — key = fileName
    const [importingFile, setImportingFile] = useState<string | null>(null);
    const [importStatus, setImportStatus] = useState<Record<string, 'success' | 'error'>>({});
    const [importMessage, setImportMessage] = useState<string | null>(null);

    // Access-denied modal
    const [accessDeniedFile, setAccessDeniedFile] = useState<LibraryFile | null>(null);

    const fetchFiles = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await getLibraryFiles();
            setFiles(data);
        } catch (e: any) {
            setError(e.message || 'Failed to load library files. Make sure the CSV Library server is running on port 5000.');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { fetchFiles(); }, [fetchFiles]);

    // ---- helpers ----
    const canAccess = (file: LibraryFile) => isAdmin || file.tag === 'User';

    const handlePreview = async (file: LibraryFile) => {
        if (!canAccess(file)) {
            setAccessDeniedFile(file);
            return;
        }
        setPreviewFile(file);
        setPreviewData(null);
        setPreviewError(null);
        setPreviewLoading(true);
        try {
            const data = await previewLibraryFile(file.fileName);
            setPreviewData(data);
        } catch (e: any) {
            setPreviewError(e.message || 'Failed to load preview');
        } finally {
            setPreviewLoading(false);
        }
    };

    const handleDownload = (file: LibraryFile) => {
        if (!canAccess(file)) {
            setAccessDeniedFile(file);
            return;
        }
        // Open the external download URL directly
        window.open(`http://localhost:5000/api/download/${encodeURIComponent(file.fileName)}`, '_blank');
    };

    const handleImport = async (file: LibraryFile) => {
        if (!canAccess(file)) {
            setAccessDeniedFile(file);
            return;
        }
        setImportingFile(file.fileName);
        setImportMessage(null);
        try {
            const newDataset = await importLibraryFile(file.fileName);
            setImportStatus(prev => ({ ...prev, [file.fileName]: 'success' }));
            setImportMessage(`"${file.fileName}" imported successfully as "${newDataset.name}"`);
            onImportSuccess?.(newDataset.name);
        } catch (e: any) {
            setImportStatus(prev => ({ ...prev, [file.fileName]: 'error' }));
            setImportMessage(e.message || 'Import failed');
        } finally {
            setImportingFile(null);
        }
    };

    // ---- render ----
    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white">CSV Library</h2>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        Datasets uploaded from the CSV Library app. {!isAdmin && 'Admin-tagged files are restricted.'}
                    </p>
                </div>
                <button
                    onClick={fetchFiles}
                    className="flex items-center gap-2 px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition"
                >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Refresh
                </button>
            </div>

            {/* Import status banner */}
            {importMessage && (
                <div className={`px-4 py-3 rounded-lg text-sm font-medium flex items-center justify-between ${
                    Object.values(importStatus).includes('error')
                        ? 'bg-red-50 text-red-700 border border-red-200'
                        : 'bg-green-50 text-green-700 border border-green-200'
                }`}>
                    <span>{importMessage}</span>
                    <button onClick={() => setImportMessage(null)} className="ml-4 text-current opacity-60 hover:opacity-100">✕</button>
                </div>
            )}

            {/* Loading */}
            {loading && (
                <div className="flex justify-center items-center h-64">
                    <Spinner />
                </div>
            )}

            {/* Error */}
            {!loading && error && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-4 rounded-lg">
                    <p className="font-semibold">Unable to connect to CSV Library</p>
                    <p className="text-sm mt-1">{error}</p>
                </div>
            )}

            {/* Empty */}
            {!loading && !error && files.length === 0 && (
                <div className="text-center py-16 text-gray-400 dark:text-gray-500">
                    <svg className="w-12 h-12 mx-auto mb-3 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
                    </svg>
                    <p>No files available in the library yet.</p>
                </div>
            )}

            {/* File grid */}
            {!loading && !error && files.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {files.map((file) => {
                        const restricted = !canAccess(file);
                        const imported = importStatus[file.fileName] === 'success';
                        const failed = importStatus[file.fileName] === 'error';
                        const isImporting = importingFile === file.fileName;

                        return (
                            <div
                                key={file.fileName}
                                className={`relative bg-white dark:bg-gray-800 rounded-xl border shadow-sm transition-all ${
                                    restricted
                                        ? 'border-red-200 dark:border-red-800 opacity-80'
                                        : 'border-gray-200 dark:border-gray-700 hover:shadow-md'
                                }`}
                            >
                                {/* Restricted overlay badge */}
                                {restricted && (
                                    <div className="absolute top-3 right-3 flex items-center gap-1 bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400 text-xs font-semibold px-2 py-0.5 rounded-full">
                                        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                                            <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                                        </svg>
                                        Restricted
                                    </div>
                                )}

                                <div className="p-5">
                                    {/* File name & tag */}
                                    <div className="flex items-start gap-3">
                                        <div className={`p-2 rounded-lg flex-shrink-0 ${restricted ? 'bg-red-50 dark:bg-red-900/20' : 'bg-blue-50 dark:bg-blue-900/20'}`}>
                                            <svg className={`w-6 h-6 ${restricted ? 'text-red-400' : 'text-blue-500'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                            </svg>
                                        </div>
                                        <div className="min-w-0 flex-1">
                                            <p className="font-semibold text-gray-900 dark:text-white text-sm truncate" title={file.fileName}>
                                                {file.fileName}
                                            </p>
                                            <div className="flex items-center gap-2 mt-1">
                                                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                                                    file.tag === 'Admin'
                                                        ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                                                        : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                                                }`}>
                                                    {file.tag}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Meta */}
                                    <div className="mt-4 grid grid-cols-2 gap-2 text-xs text-gray-500 dark:text-gray-400">
                                        <div>
                                            <span className="block text-gray-400">Rows</span>
                                            <span className="font-medium text-gray-700 dark:text-gray-300">{file.rowCount.toLocaleString()}</span>
                                        </div>
                                        <div>
                                            <span className="block text-gray-400">Uploaded</span>
                                            <span className="font-medium text-gray-700 dark:text-gray-300">
                                                {new Date(file.uploadedAt).toLocaleDateString()}
                                            </span>
                                        </div>
                                    </div>

                                    {/* Import success indicator */}
                                    {imported && (
                                        <div className="mt-3 text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
                                            <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                                            </svg>
                                            Imported into your workspace
                                        </div>
                                    )}
                                    {failed && (
                                        <div className="mt-3 text-xs text-red-600 dark:text-red-400 flex items-center gap-1">
                                            <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                                                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd"/>
                                            </svg>
                                            Import failed — try again
                                        </div>
                                    )}

                                    {/* Action buttons */}
                                    <div className="mt-4 flex gap-2">
                                        {/* Preview */}
                                        <button
                                            onClick={() => handlePreview(file)}
                                            className={`flex-1 text-xs font-medium py-1.5 px-2 rounded-lg transition ${
                                                restricted
                                                    ? 'bg-gray-100 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
                                                    : 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/40'
                                            }`}
                                        >
                                            {restricted ? '🔒 Preview' : 'Preview'}
                                        </button>

                                        {/* Download */}
                                        <button
                                            onClick={() => handleDownload(file)}
                                            className={`flex-1 text-xs font-medium py-1.5 px-2 rounded-lg transition ${
                                                restricted
                                                    ? 'bg-gray-100 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
                                                    : 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900/40'
                                            }`}
                                        >
                                            {restricted ? '🔒 Download' : 'Download'}
                                        </button>

                                        {/* Import (only for regular users, admins don't need it in their panel) */}
                                        {!isAdmin && (
                                            <button
                                                onClick={() => handleImport(file)}
                                                disabled={isImporting || imported || restricted}
                                                className={`flex-1 text-xs font-medium py-1.5 px-2 rounded-lg transition ${
                                                    restricted
                                                        ? 'bg-gray-100 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
                                                        : imported
                                                        ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 cursor-default'
                                                        : 'bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-900/40 disabled:opacity-50'
                                                }`}
                                            >
                                                {isImporting ? (
                                                    <span className="flex items-center justify-center gap-1">
                                                        <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                                                        </svg>
                                                        Importing…
                                                    </span>
                                                ) : imported ? '✓ Imported' : restricted ? '🔒 Import' : 'Import'}
                                            </button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Preview Modal */}
            {previewFile && (
                <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
                    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl w-full max-w-5xl max-h-[90vh] flex flex-col">
                        {/* Modal Header */}
                        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between flex-shrink-0">
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{previewFile.fileName}</h3>
                                <div className="flex items-center gap-2 mt-0.5">
                                    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                                        previewFile.tag === 'Admin'
                                            ? 'bg-red-100 text-red-700'
                                            : 'bg-green-100 text-green-700'
                                    }`}>{previewFile.tag}</span>
                                    <span className="text-xs text-gray-400">First 20 rows of {previewFile.rowCount.toLocaleString()} total</span>
                                </div>
                            </div>
                            <button
                                onClick={() => { setPreviewFile(null); setPreviewData(null); }}
                                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 p-1"
                            >
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12"/>
                                </svg>
                            </button>
                        </div>

                        {/* Modal Body */}
                        <div className="overflow-auto flex-1 p-4">
                            {previewLoading && (
                                <div className="flex justify-center items-center h-40"><Spinner /></div>
                            )}
                            {previewError && (
                                <div className="text-red-600 dark:text-red-400 text-sm p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">{previewError}</div>
                            )}
                            {previewData && (
                                <div className="overflow-x-auto">
                                    <table className="min-w-full text-sm divide-y divide-gray-200 dark:divide-gray-700">
                                        <thead className="bg-gray-50 dark:bg-gray-800 sticky top-0">
                                            <tr>
                                                {previewData.columns.map((col, i) => (
                                                    <th key={i} className="px-4 py-2 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider whitespace-nowrap">
                                                        {col}
                                                    </th>
                                                ))}
                                            </tr>
                                        </thead>
                                        <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-100 dark:divide-gray-800">
                                            {previewData.rows.map((row, ri) => (
                                                <tr key={ri} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                                                    {previewData.columns.map((col, ci) => (
                                                        <td key={ci} className="px-4 py-2 whitespace-nowrap text-gray-700 dark:text-gray-300">
                                                            {row[col] !== null && row[col] !== undefined ? String(row[col]) : '—'}
                                                        </td>
                                                    ))}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Access Denied Modal */}
            {accessDeniedFile && (
                <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
                    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl w-full max-w-sm p-6 text-center">
                        <div className="w-14 h-14 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                            <svg className="w-7 h-7 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd"/>
                            </svg>
                        </div>
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white">Access Denied</h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                            <span className="font-medium text-gray-700 dark:text-gray-300">"{accessDeniedFile.fileName}"</span> is tagged as{' '}
                            <span className="font-semibold text-red-600">Admin</span> and is restricted to administrators only.
                        </p>
                        <button
                            onClick={() => setAccessDeniedFile(null)}
                            className="mt-5 w-full py-2 bg-gray-900 dark:bg-white dark:text-gray-900 text-white rounded-lg text-sm font-semibold hover:opacity-90 transition"
                        >
                            Close
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};
