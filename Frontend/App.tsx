import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { QueryInput } from './components/QueryInput';
import { ResultsDisplay } from './components/ResultsDisplay';
import { DataIngestionModal } from './components/DataIngestionModal';
import { WelcomeScreen } from './components/WelcomeScreen';
import { Login } from './components/Login';
import { Signup } from './components/Signup';
import { OTPVerification } from './components/OTPVerification';
import { translateToMongoQuery } from './services/geminiService';
import { 
    getDatasets, 
    runQuery, 
    uploadDataset as apiUploadDataset,
    login as apiLogin,
    signup as apiSignup,
    verifyOTP as apiVerifyOTP,
    resendOTP as apiResendOTP,
    logout as apiLogout,
    getAuthToken,
    getUserData,
    verifyToken
} from './services/apiService';
import type { DataSet, QueryResult, ChartData } from './types';
import { QueryMode } from './types';

const App: React.FC = () => {
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
    const [currentUser, setCurrentUser] = useState<any>(null);
    const [authView, setAuthView] = useState<'login' | 'signup' | 'otp'>('login');
    const [pendingEmail, setPendingEmail] = useState<string>('');
    const [authLoading, setAuthLoading] = useState<boolean>(false);
    const [authError, setAuthError] = useState<string | null>(null);
    const [isCheckingAuth, setIsCheckingAuth] = useState<boolean>(true);

    const [datasets, setDatasets] = useState<DataSet[]>([]);
    const [selectedDataset, setSelectedDataset] = useState<DataSet | null>(null);
    const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [isUploading, setIsUploading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
    const [chartData, setChartData] = useState<ChartData[]>([]);

    // Check authentication on mount
    useEffect(() => {
        const checkAuth = async () => {
            const token = getAuthToken();
            const user = getUserData();
            
            if (token && user) {
                const isValid = await verifyToken();
                if (isValid) {
                    setIsAuthenticated(true);
                    setCurrentUser(user);
                } else {
                    apiLogout();
                    setIsAuthenticated(false);
                    setCurrentUser(null);
                }
            }
            setIsCheckingAuth(false);
        };
        
        checkAuth();
    }, []);

    useEffect(() => {
        if (isAuthenticated) {
            const fetchInitialData = async () => {
                try {
                    setIsLoading(true);
                    const initialDatasets = await getDatasets();
                    setDatasets(initialDatasets);
                } catch (err: any) {
                    if (err.message.includes('Session expired')) {
                        setIsAuthenticated(false);
                        setCurrentUser(null);
                        setError('Your session has expired. Please login again.');
                    } else {
                        setError('Failed to load initial datasets.');
                    }
                    console.error('Error loading datasets:', err);
                } finally {
                    setIsLoading(false);
                }
            };
            fetchInitialData();
        }
    }, [isAuthenticated]);

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
            
            if (mode === QueryMode.NL) {
                console.log("Processing Natural Language query:", query);
                try {
                    const frontendTranslated = await translateToMongoQuery(query, selectedDataset.schema);
                    if (frontendTranslated !== query && frontendTranslated !== '[{"$limit": 10}]') {
                        executedQuery = frontendTranslated;
                        console.log("Using frontend-translated query:", executedQuery);
                    } else {
                        executedQuery = query;
                        console.log("Delegating translation to backend");
                    }
                } catch (err) {
                    console.log("Frontend translation failed, using backend:", err);
                    executedQuery = query;
                }
            }
            
            const result = await runQuery(selectedDataset.id, executedQuery, mode);
            setQueryResult(result);
            
            if (mode === QueryMode.NL && result.rows && result.rows.length > 0) {
                console.log("Natural language query executed successfully");
            }
            
        } catch (err: any) {
            console.error('Query execution error:', err);
            if (err.message.includes('Session expired')) {
                setIsAuthenticated(false);
                setCurrentUser(null);
            }
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
        } catch (err: any) {
            if (err.message.includes('Session expired')) {
                setIsAuthenticated(false);
                setCurrentUser(null);
            }
            setError(err instanceof Error ? err.message : 'Failed to upload dataset.');
        } finally {
            setIsUploading(false);
        }
    };

    const handleLogin = async (email: string, password: string) => {
        setAuthLoading(true);
        setAuthError(null);
        try {
            const { user } = await apiLogin(email, password);
            setIsAuthenticated(true);
            setCurrentUser(user);
        } catch (err: any) {
            setAuthError(err.message || 'Login failed. Please try again.');
        } finally {
            setAuthLoading(false);
        }
    };

    const handleSignup = async (name: string, email: string, password: string) => {
        setAuthLoading(true);
        setAuthError(null);
        try {
            await apiSignup(name, email, password);
            setPendingEmail(email);
            setAuthView('otp');
        } catch (err: any) {
            setAuthError(err.message || 'Signup failed. Please try again.');
        } finally {
            setAuthLoading(false);
        }
    };

    const handleVerifyOTP = async (email: string, otp: string) => {
        setAuthLoading(true);
        setAuthError(null);
        try {
            const { user } = await apiVerifyOTP(email, otp);
            setIsAuthenticated(true);
            setCurrentUser(user);
            setPendingEmail('');
        } catch (err: any) {
            setAuthError(err.message || 'OTP verification failed. Please try again.');
        } finally {
            setAuthLoading(false);
        }
    };

    const handleResendOTP = async (email: string) => {
        await apiResendOTP(email);
    };

    const handleLogout = () => {
        apiLogout();
        setIsAuthenticated(false);
        setCurrentUser(null);
        setDatasets([]);
        setSelectedDataset(null);
        setQueryResult(null);
    };

    if (isCheckingAuth) {
        return (
            <div className="flex items-center justify-center h-screen bg-gray-100 dark:bg-gray-900">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600 dark:text-gray-400">Loading...</p>
                </div>
            </div>
        );
    }

    if (!isAuthenticated) {
        if (authView === 'login') {
            return (
                <Login
                    onLogin={handleLogin}
                    onSwitchToSignup={() => {
                        setAuthView('signup');
                        setAuthError(null);
                    }}
                    isLoading={authLoading}
                    error={authError}
                />
            );
        } else if (authView === 'signup') {
            return (
                <Signup
                    onSignup={handleSignup}
                    onSwitchToLogin={() => {
                        setAuthView('login');
                        setAuthError(null);
                    }}
                    isLoading={authLoading}
                    error={authError}
                />
            );
        } else {
            return (
                <OTPVerification
                    email={pendingEmail}
                    onVerify={handleVerifyOTP}
                    onResendOTP={handleResendOTP}
                    onBack={() => {
                        setAuthView('signup');
                        setAuthError(null);
                        setPendingEmail('');
                    }}
                    isLoading={authLoading}
                    error={authError}
                />
            );
        }
    }

    return (
        <div className="flex flex-col h-screen font-sans text-gray-900 dark:text-gray-100 bg-gray-100 dark:bg-gray-900">
            <Header user={currentUser} onLogout={handleLogout} />
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
