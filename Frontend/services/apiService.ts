
import type { DataSet, QueryResult, QueryMode } from '../types';
import { MOCK_DATASETS, MOCK_QUERY_RESULT } from '../constants';

// API base URL
const API_BASE_URL = 'http://localhost:5001/api';

// Use mock data for development if API is unreachable
let useMockData = false;

// Token management
const TOKEN_KEY = 'auth_token';
const USER_KEY = 'user_data';

export const setAuthToken = (token: string) => {
    localStorage.setItem(TOKEN_KEY, token);
};

export const getAuthToken = (): string | null => {
    return localStorage.getItem(TOKEN_KEY);
};

export const removeAuthToken = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
};

export const setUserData = (user: any) => {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
};

export const getUserData = (): any | null => {
    const data = localStorage.getItem(USER_KEY);
    return data ? JSON.parse(data) : null;
};

// Auth API functions
export const signup = async (name: string, email: string, password: string): Promise<{ email: string }> => {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/signup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, email, password })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Signup failed');
        }

        const data = await response.json();
        return { email: data.email };
    } catch (error) {
        console.error('Error during signup:', error);
        throw error;
    }
};

export const verifyOTP = async (email: string, otp: string): Promise<{ user: any; token: string }> => {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/verify-otp`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, otp })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'OTP verification failed');
        }

        const data = await response.json();
        setAuthToken(data.access_token);
        setUserData(data.user);
        return { user: data.user, token: data.access_token };
    } catch (error) {
        console.error('Error during OTP verification:', error);
        throw error;
    }
};

export const resendOTP = async (email: string): Promise<void> => {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/resend-otp`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to resend OTP');
        }
    } catch (error) {
        console.error('Error resending OTP:', error);
        throw error;
    }
};

export const login = async (email: string, password: string): Promise<{ user: any; token: string }> => {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Login failed');
        }

        const data = await response.json();
        setAuthToken(data.access_token);
        setUserData(data.user);
        return { user: data.user, token: data.access_token };
    } catch (error) {
        console.error('Error during login:', error);
        throw error;
    }
};

export const logout = () => {
    removeAuthToken();
};

export const verifyToken = async (): Promise<boolean> => {
    const token = getAuthToken();
    if (!token) return false;

    try {
        const response = await fetch(`${API_BASE_URL}/auth/verify`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        return response.ok;
    } catch (error) {
        console.error('Error verifying token:', error);
        return false;
    }
};

// Simulate network latency for development
const delay = (ms: number) => new Promise(res => setTimeout(res, ms));

// Helper function to check if API is reachable
const checkApiConnection = async (): Promise<boolean> => {
    try {
        const response = await fetch(`${API_BASE_URL}/health`, { method: 'GET' });
        return response.ok;
    } catch (error) {
        console.warn('Backend API not reachable, using mock data instead');
        return false;
    }
};

export const getDatasets = async (): Promise<DataSet[]> => {
    // Check API connection on first request
    if (useMockData === false) {
        useMockData = !(await checkApiConnection());
    }

    if (useMockData) {
        await delay(500);
        return MOCK_DATASETS;
    }

    try {
        const token = getAuthToken();
        const response = await fetch(`${API_BASE_URL}/datasets`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) {
            if (response.status === 401) {
                removeAuthToken();
                throw new Error('Session expired. Please login again.');
            }
            throw new Error(`Failed to fetch datasets: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching datasets:', error);
        throw error;
    }
};

export const runQuery = async (
    datasetId: string,
    query: string,
    mode: QueryMode
): Promise<QueryResult> => {
    if (useMockData) {
        await delay(1500);
        console.log(`Executing query on ${datasetId} in ${mode} mode:`, query);

        if (datasetId in MOCK_QUERY_RESULT) {
            const result = MOCK_QUERY_RESULT[datasetId as keyof typeof MOCK_QUERY_RESULT];
            return { ...result, query };
        }
        
        // Return a generic success response if dataset is not in mock results
        return {
            columns: ['status', 'message'],
            rows: [{ status: 'success', message: 'Query executed but no mock data available.' }],
            query: query
        };
    }

    try {
        const token = getAuthToken();
        const response = await fetch(`${API_BASE_URL}/queries/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                datasetId: datasetId,
                query: query,
                mode: mode
            })
        });

        if (!response.ok) {
            if (response.status === 401) {
                removeAuthToken();
                throw new Error('Session expired. Please login again.');
            }
            const errorData = await response.json();
            throw new Error(errorData.error || `Query failed: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error running query:', error);
        throw error;
    }
};

export const uploadDataset = async (
    file: File,
    name: string,
    description: string
): Promise<DataSet> => {
    if (useMockData) {
        await delay(2000);
        console.log(`Uploading file: ${file.name}, Dataset name: ${name}`);
        
        // Simulate failure
        if (name.toLowerCase().includes('fail')) {
            throw new Error("Simulated upload failure.");
        }

        // Simulate success and return a new dataset object
        const newDataset: DataSet = {
            id: `custom_${Date.now()}`,
            name: name,
            description: description,
            schema: {
                "col_a": "string",
                "col_b": "number",
                "col_c": "boolean"
            }
        };
        return newDataset;
    }

    try {
        const token = getAuthToken();
        const formData = new FormData();
        formData.append('file', file);
        formData.append('name', name);
        formData.append('description', description);

        const response = await fetch(`${API_BASE_URL}/datasets`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        if (!response.ok) {
            if (response.status === 401) {
                removeAuthToken();
                throw new Error('Session expired. Please login again.');
            }
            const errorData = await response.json();
            throw new Error(errorData.error || `Upload failed: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error uploading dataset:', error);
        throw error;
    }
};

export const deleteDataset = async (datasetId: string): Promise<void> => {
    if (useMockData) {
        await delay(500);
        console.log(`Deleting dataset: ${datasetId}`);
        return;
    }

    try {
        const token = getAuthToken();
        const response = await fetch(`${API_BASE_URL}/datasets/${datasetId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                removeAuthToken();
                throw new Error('Session expired. Please login again.');
            }
            const errorData = await response.json();
            throw new Error(errorData.error || `Delete failed: ${response.statusText}`);
        }
    } catch (error) {
        console.error('Error deleting dataset:', error);
        throw error;
    }
};

export const downloadDatasetAdmin = async (datasetId: string, filename: string): Promise<void> => {
    try {
        const token = getAuthToken();
        const response = await fetch(`${API_BASE_URL}/admin/datasets/${datasetId}/download`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                removeAuthToken();
                throw new Error('Session expired. Please login again.');
            }
            // Read actual error message from backend
            try {
                const errorData = await response.json();
                throw new Error(errorData.error || `Failed to download (${response.status})`);
            } catch {
                throw new Error(`Failed to download dataset (HTTP ${response.status})`);
            }
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        console.error('Error downloading dataset:', error);
        throw error;
    }
};

export const previewDatasetAdmin = async (datasetId: string): Promise<any> => {
    try {
        const token = getAuthToken();
        const response = await fetch(`${API_BASE_URL}/admin/datasets/${datasetId}/preview`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                removeAuthToken();
                throw new Error('Session expired. Please login again.');
            }
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to preview dataset');
        }

        return await response.json();
    } catch (error) {
        console.error('Error previewing dataset:', error);
        throw error;
    }
};
// Admin API functions
export const getAllUsers = async (): Promise<any> => {
    try {
        const token = getAuthToken();
        const response = await fetch(`${API_BASE_URL}/admin/users`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                removeAuthToken();
                throw new Error('Session expired. Please login again.');
            }
            if (response.status === 403) {
                throw new Error('Admin access required');
            }
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to fetch users');
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching users:', error);
        throw error;
    }
};

export const getAllDatasetsAdmin = async (): Promise<any> => {
    try {
        const token = getAuthToken();
        const response = await fetch(`${API_BASE_URL}/admin/datasets`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                removeAuthToken();
                throw new Error('Session expired. Please login again.');
            }
            if (response.status === 403) {
                throw new Error('Admin access required');
            }
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to fetch datasets');
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching datasets:', error);
        throw error;
    }
};

export const getAdminStats = async (): Promise<any> => {
    try {
        const token = getAuthToken();
        const response = await fetch(`${API_BASE_URL}/admin/stats`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                removeAuthToken();
                throw new Error('Session expired. Please login again.');
            }
            if (response.status === 403) {
                throw new Error('Admin access required');
            }
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to fetch stats');
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching stats:', error);
        throw error;
    }
};

// ─────────────────────────────────────────────────────────────────────────────
// CSV Library — talks directly to the external CSV Library app (port 5000)
// ─────────────────────────────────────────────────────────────────────────────
const LIBRARY_BASE_URL = 'http://localhost:5000/api';

/** Get the list of all uploaded CSV files in the shared library. */
export const getLibraryFiles = async (): Promise<any[]> => {
    const response = await fetch(`${LIBRARY_BASE_URL}/files`);
    if (!response.ok) {
        throw new Error(`Library server error (${response.status}). Is the CSV Library running on port 5000?`);
    }
    const data = await response.json();
    return data.files ?? [];
};

/** Get the first 20 rows of a library file for preview. */
export const previewLibraryFile = async (fileName: string): Promise<{ columns: string[]; rows: any[] }> => {
    const url = `${LIBRARY_BASE_URL}/data?fileName=${encodeURIComponent(fileName)}&limit=20&page=1`;
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Failed to load preview (${response.status})`);
    }
    const data = await response.json();
    const rows: any[] = (data.data ?? []).map((rec: any) => rec.data ?? rec);
    const columns: string[] = rows.length > 0 ? Object.keys(rows[0]) : [];
    return { columns, rows };
};

/**
 * Download a file from the library and re-upload it into Query Mitra as a
 * personal dataset for the currently logged-in user.
 */
export const importLibraryFile = async (fileName: string): Promise<DataSet> => {
    // 1. Fetch the raw CSV from the external library
    const downloadUrl = `${LIBRARY_BASE_URL}/download/${encodeURIComponent(fileName)}`;
    const downloadResponse = await fetch(downloadUrl);
    if (!downloadResponse.ok) {
        throw new Error(`Failed to download library file (${downloadResponse.status})`);
    }
    const blob = await downloadResponse.blob();
    const file = new File([blob], fileName, { type: 'text/csv' });

    // 2. Upload it into this app's backend under the authenticated user
    const nameWithoutExt = fileName.replace(/\.[^/.]+$/, '');
    return uploadDataset(file, nameWithoutExt, `Imported from CSV Library: ${fileName}`);
};