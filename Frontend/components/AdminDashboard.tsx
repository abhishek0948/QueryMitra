import React, { useState, useEffect } from 'react';
import { getAllUsers, getAllDatasetsAdmin, getAdminStats, downloadDatasetAdmin, previewDatasetAdmin } from '../services/apiService';
import { LibrarySection } from './LibrarySection';

interface User {
    id: string;
    name: string;
    email: string;
    role: string;
    created_at: string;
    datasets?: any[];
    dataset_count?: number;
}

interface Dataset {
    id: string;
    name: string;
    description: string;
    user_id: string;
    user_name: string;
    user_email: string;
    created_at: string;
    filename?: string;
}

interface Stats {
    total_users: number;
    admin_users: number;
    regular_users: number;
    total_datasets: number;
    recent_users: User[];
}

interface PreviewData {
    columns: string[];
    rows: any[];
    total_rows_in_file: number;
    total_columns: number;
}

export const AdminDashboard: React.FC<{ onLogout: () => void }> = ({ onLogout }) => {
    const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'datasets' | 'library'>('overview');
    const [users, setUsers] = useState<User[]>([]);
    const [datasets, setDatasets] = useState<Dataset[]>([]);
    const [stats, setStats] = useState<Stats | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [previewData, setPreviewData] = useState<PreviewData | null>(null);
    const [showPreviewModal, setShowPreviewModal] = useState<boolean>(false);
    const [previewLoading, setPreviewLoading] = useState<boolean>(false);

    useEffect(() => {
        loadData();
    }, [activeTab]);

    const loadData = async () => {
        // LibrarySection manages its own data fetching
        if (activeTab === 'library') return;

        setLoading(true);
        setError(null);
        try {
            if (activeTab === 'overview') {
                const statsData = await getAdminStats();
                setStats(statsData);
            } else if (activeTab === 'users') {
                const usersData = await getAllUsers();
                setUsers(usersData.users);
            } else if (activeTab === 'datasets') {
                const datasetsData = await getAllDatasetsAdmin();
                setDatasets(datasetsData.datasets);
            }
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handlePreview = async (datasetId: string) => {
        setPreviewLoading(true);
        setError(null);
        try {
            const data = await previewDatasetAdmin(datasetId);
            setPreviewData(data);
            setShowPreviewModal(true);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setPreviewLoading(false);
        }
    };

    const handleDownload = async (datasetId: string, filename: string) => {
        setError(null);
        try {
            await downloadDatasetAdmin(datasetId, filename);
        } catch (err: any) {
            setError(err.message);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <div className="bg-white shadow-md">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center py-4">
                        <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
                        <button
                            onClick={onLogout}
                            className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition"
                        >
                            Logout
                        </button>
                    </div>
                </div>
            </div>

            {/* Navigation Tabs */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
                <div className="border-b border-gray-200">
                    <nav className="-mb-px flex space-x-8">
                        <button
                            onClick={() => setActiveTab('overview')}
                            className={`${
                                activeTab === 'overview'
                                    ? 'border-indigo-500 text-indigo-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
                        >
                            Overview
                        </button>
                        <button
                            onClick={() => setActiveTab('users')}
                            className={`${
                                activeTab === 'users'
                                    ? 'border-indigo-500 text-indigo-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
                        >
                            Users
                        </button>
                        <button
                            onClick={() => setActiveTab('datasets')}
                            className={`${
                                activeTab === 'datasets'
                                    ? 'border-indigo-500 text-indigo-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
                        >
                            All Datasets
                        </button>
                        <button
                            onClick={() => setActiveTab('library')}
                            className={`${
                                activeTab === 'library'
                                    ? 'border-indigo-500 text-indigo-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
                        >
                            CSV Library
                        </button>
                    </nav>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {loading ? (
                    <div className="flex justify-center items-center h-64">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
                    </div>
                ) : error ? (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                        {error}
                    </div>
                ) : (
                    <>
                        {activeTab === 'overview' && stats && (
                            <div className="space-y-6">
                                {/* Stats Grid */}
                                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                                    <div className="bg-white p-6 rounded-lg shadow">
                                        <div className="text-sm text-gray-500">Total Users</div>
                                        <div className="text-3xl font-bold text-gray-900 mt-2">{stats.total_users}</div>
                                    </div>
                                    <div className="bg-white p-6 rounded-lg shadow">
                                        <div className="text-sm text-gray-500">Admin Users</div>
                                        <div className="text-3xl font-bold text-indigo-600 mt-2">{stats.admin_users}</div>
                                    </div>
                                    <div className="bg-white p-6 rounded-lg shadow">
                                        <div className="text-sm text-gray-500">Regular Users</div>
                                        <div className="text-3xl font-bold text-green-600 mt-2">{stats.regular_users}</div>
                                    </div>
                                    <div className="bg-white p-6 rounded-lg shadow">
                                        <div className="text-sm text-gray-500">Total Datasets</div>
                                        <div className="text-3xl font-bold text-purple-600 mt-2">{stats.total_datasets}</div>
                                    </div>
                                </div>

                                {/* Recent Users */}
                                <div className="bg-white rounded-lg shadow">
                                    <div className="px-6 py-4 border-b border-gray-200">
                                        <h2 className="text-lg font-semibold text-gray-900">Recent Users</h2>
                                    </div>
                                    <div className="overflow-x-auto">
                                        <table className="min-w-full divide-y divide-gray-200">
                                            <thead className="bg-gray-50">
                                                <tr>
                                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Joined</th>
                                                </tr>
                                            </thead>
                                            <tbody className="bg-white divide-y divide-gray-200">
                                                {stats.recent_users.map((user) => (
                                                    <tr key={user.id}>
                                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{user.name}</td>
                                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{user.email}</td>
                                                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                                                            <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                                                                user.role === 'admin' ? 'bg-indigo-100 text-indigo-800' : 'bg-green-100 text-green-800'
                                                            }`}>
                                                                {user.role || 'user'}
                                                            </span>
                                                        </td>
                                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                            {new Date(user.created_at).toLocaleDateString()}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === 'users' && (
                            <div className="bg-white rounded-lg shadow">
                                <div className="px-6 py-4 border-b border-gray-200">
                                    <h2 className="text-lg font-semibold text-gray-900">All Users</h2>
                                </div>
                                <div className="overflow-x-auto">
                                    <table className="min-w-full divide-y divide-gray-200">
                                        <thead className="bg-gray-50">
                                            <tr>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Datasets</th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Joined</th>
                                            </tr>
                                        </thead>
                                        <tbody className="bg-white divide-y divide-gray-200">
                                            {users.map((user) => (
                                                <tr key={user.id} className="hover:bg-gray-50">
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{user.name}</td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{user.email}</td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                                                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                                                            user.role === 'admin' ? 'bg-indigo-100 text-indigo-800' : 'bg-green-100 text-green-800'
                                                        }`}>
                                                            {user.role}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                        {user.dataset_count || 0}
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                        {new Date(user.created_at).toLocaleDateString()}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}

                        {activeTab === 'library' && (
                            <div className="bg-white rounded-lg shadow">
                                <LibrarySection isAdmin />
                            </div>
                        )}

                        {activeTab === 'datasets' && (
                            <div className="bg-white rounded-lg shadow">
                                <div className="px-6 py-4 border-b border-gray-200">
                                    <h2 className="text-lg font-semibold text-gray-900">All Datasets</h2>
                                </div>
                                <div className="overflow-x-auto">
                                    <table className="min-w-full divide-y divide-gray-200">
                                        <thead className="bg-gray-50">
                                            <tr>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dataset Name</th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Owner</th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody className="bg-white divide-y divide-gray-200">
                                            {datasets.map((dataset) => (
                                                <tr key={dataset.id} className="hover:bg-gray-50">
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{dataset.name}</td>
                                                    <td className="px-6 py-4 text-sm text-gray-500">{dataset.description}</td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                        <div>{dataset.user_name}</div>
                                                        <div className="text-xs text-gray-400">{dataset.user_email}</div>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                        {new Date(dataset.created_at).toLocaleDateString()}
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                        <div className="flex space-x-2">
                                                            <button
                                                                onClick={() => handlePreview(dataset.id)}
                                                                className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 transition"
                                                                disabled={previewLoading}
                                                            >
                                                                Preview
                                                            </button>
                                                            <button
                                                                onClick={() => handleDownload(dataset.id, dataset.filename || 'dataset.csv')}
                                                                className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 transition"
                                                            >
                                                                Download
                                                            </button>
                                                        </div>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>

            {/* Preview Modal */}
            {showPreviewModal && previewData && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
                        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                            <div>
                                <h2 className="text-xl font-semibold text-gray-900">Dataset Preview</h2>
                                <p className="text-sm text-gray-500">
                                    Showing first 20 rows of {previewData.total_rows_in_file} total rows
                                </p>
                            </div>
                            <button
                                onClick={() => {
                                    setShowPreviewModal(false);
                                    setPreviewData(null);
                                }}
                                className="text-gray-400 hover:text-gray-600"
                            >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>
                        <div className="p-6 overflow-auto max-h-[calc(90vh-120px)]">
                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-gray-200 text-sm">
                                    <thead className="bg-gray-50 sticky top-0">
                                        <tr>
                                            {previewData.columns.map((col, idx) => (
                                                <th key={idx} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    {col}
                                                </th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white divide-y divide-gray-200">
                                        {previewData.rows.map((row, rowIdx) => (
                                            <tr key={rowIdx} className="hover:bg-gray-50">
                                                {previewData.columns.map((col, colIdx) => (
                                                    <td key={colIdx} className="px-4 py-2 whitespace-nowrap text-gray-700">
                                                        {row[col] !== null && row[col] !== undefined ? String(row[col]) : '-'}
                                                    </td>
                                                ))}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
