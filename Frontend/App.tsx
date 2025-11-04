import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { QueryInput } from './components/QueryInput';
import { ResultsDisplay } from './components/ResultsDisplay';
import { DataIngestionModal } from './components/DataIngestionModal';
import { WelcomeScreen } from './components/WelcomeScreen';  // Ensure this import is present
import { translateToMongoQuery } from './services/geminiService';
import { getDatasets, runQuery, uploadDataset as apiUploadDataset } from './services/apiService';
import type { DataSet, QueryResult, ChartData } from './types';
import { QueryMode } from './types';

const App: React.FC = () => {
    const [datasets, setDatasets] = useState<DataSet[]>([]);
    const [selectedDataset, setSelectedDataset] = useState<DataSet | null>(null);
    const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [isUploading, setIsUploading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
    const [chartData, setChartData] = useState<ChartData[]>([]);

    useEffect(() => {
        const fetchInitialData = async () => {
            try {
                setIsLoading(true);
                const initialDatasets = await getDatasets();
                setDatasets(initialDatasets);
            } catch (err) {
                setError('Failed to load initial datasets.');
                console.error('Error loading datasets:', err);
            } finally {
                setIsLoading(false);
            }
        };
        fetchInitialData();
    }, []);

    useEffect(() => {
        if (queryResult && queryResult.rows.length > 0) {
            const newChartData = queryResult.rows.map(row => {
                const name = Object.values(row)[0] as string;
                const value = Object.values(row)[1] as number;
                return { name, value };
            }).filter(d => typeof d.name === 'string' && typeof d.value === 'number');
            setChartData(newChartData);
        } else {
            setChartData([]);
        }
    }, [queryResult]);
    
    const handleRunQuery = useCallback(async (query: string, mode: QueryMode) => {
        if (!selectedDataset) {
            setError('Please select a dataset first.');
            return;
        }

        setIsLoading(true);
        setError(null);
        setQueryResult(null);

        try {
            let executedQuery = query;
            
            // For Natural Language mode, let the backend handle the translation
            // The frontend translateToMongoQuery is kept as a fallback but mainly
            // the backend will do the heavy lifting with the Gemini API
            if (mode === QueryMode.NL) {
                console.log("Processing Natural Language query:", query);
                // Try frontend translation first (if API key is available)
                try {
                    const frontendTranslated = await translateToMongoQuery(query, selectedDataset.schema);
                    // If we got back the original query, it means frontend delegated to backend
                    if (frontendTranslated !== query && frontendTranslated !== '[{"$limit": 10}]') {
                        executedQuery = frontendTranslated;
                        console.log("Using frontend-translated query:", executedQuery);
                    } else {
                        // Let backend handle the translation
                        executedQuery = query;
                        console.log("Delegating translation to backend");
                    }
                } catch (err) {
                    console.log("Frontend translation failed, using backend:", err);
                    // Keep original query for backend to translate
                    executedQuery = query;
                }
            }
            
            const result = await runQuery(selectedDataset.id, executedQuery, mode);
            setQueryResult(result);
            
            // Show success message for NL queries
            if (mode === QueryMode.NL && result.rows && result.rows.length > 0) {
                console.log("Natural language query executed successfully");
            }
            
        } catch (err: any) {
            console.error('Query execution error:', err);
            setError(err.message || 'Query execution failed. Please check your query and try again.');
        } finally {
            setIsLoading(false);
        }
    }, [selectedDataset]);

    const handleUploadDataset = async (file: File, name: string, description: string) => {
        setIsUploading(true);
        setError(null);
        try {
            const newDataset = await apiUploadDataset(file, name, description);
            setDatasets(prev => [...prev, newDataset]);
            setSelectedDataset(newDataset);
            setIsModalOpen(false);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to upload dataset.');
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="flex flex-col h-screen font-sans text-gray-900 dark:text-gray-100 bg-gray-100 dark:bg-gray-900">
            <Header />
            <div className="flex flex-1 overflow-hidden">
                <Sidebar
                    datasets={datasets}
                    selectedDatasetId={selectedDataset?.id}
                    onSelectDataset={id => {
                        setSelectedDataset(datasets.find(d => d.id === id) || null);
                        setQueryResult(null);
                        setError(null);
                    }}
                    onUploadClick={() => setIsModalOpen(true)}
                />
                <main className="flex-1 flex flex-col p-6 overflow-auto">
                    {selectedDataset ? (
                      <>
                        <QueryInput dataset={selectedDataset} onRunQuery={handleRunQuery} isLoading={isLoading} />
                        <ResultsDisplay result={queryResult} isLoading={isLoading} error={error} chartData={chartData} />
                      </>
                    ) : (
                      <WelcomeScreen onUploadClick={() => setIsModalOpen(true)} />
                    )}
                </main>
            </div>
            {isModalOpen && (
                <DataIngestionModal
                    onClose={() => setIsModalOpen(false)}
                    onUpload={handleUploadDataset}
                    isLoading={isUploading}
                />
            )}
        </div>
    );
};

export default App;
