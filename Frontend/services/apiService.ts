
import type { DataSet, QueryResult, QueryMode } from '../types';
import { MOCK_DATASETS, MOCK_QUERY_RESULT } from '../constants';

// API base URL
const API_BASE_URL = 'http://localhost:5000/api';

// Use mock data for development if API is unreachable
let useMockData = false;

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
        const response = await fetch(`${API_BASE_URL}/datasets`);
        if (!response.ok) {
            throw new Error(`Failed to fetch datasets: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching datasets:', error);
        // Fall back to mock data if API call fails
        return MOCK_DATASETS;
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
        const response = await fetch(`${API_BASE_URL}/queries/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                datasetId: datasetId,
                query: query,
                mode: mode
            })
        });

        if (!response.ok) {
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
        const formData = new FormData();
        formData.append('file', file);
        formData.append('name', name);
        formData.append('description', description);

        const response = await fetch(`${API_BASE_URL}/datasets`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Upload failed: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error uploading dataset:', error);
        throw error;
    }
};
