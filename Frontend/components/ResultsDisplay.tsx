
import React, { useState } from 'react';
import type { QueryResult, ChartData } from '../types';
import { ViewMode } from '../types';
import { BarChartComponent } from './charts/BarChartComponent';
import { PieChartComponent } from './charts/PieChartComponent';
import { IconTable } from './icons/IconTable';
import { IconChartBar } from './icons/IconChartBar';
import { IconCode } from './icons/IconCode';
import { Spinner } from './Spinner';

interface ResultsDisplayProps {
    result: QueryResult | null;
    isLoading: boolean;
    error: string | null;
    chartData: ChartData[];
}

const ChartView: React.FC<{ data: ChartData[] }> = ({ data }) => {
    const [chartType, setChartType] = useState<'bar' | 'pie'>('bar');

    if (data.length === 0) {
        return <div className="text-center p-8 text-gray-500">No data suitable for charting. Charts require at least one text column and one numeric column.</div>
    }

    return (
        <div>
            <div className="mb-4 flex justify-center space-x-2">
                 <button onClick={() => setChartType('bar')} className={`px-4 py-2 text-sm font-medium rounded-md ${chartType === 'bar' ? 'bg-blue-500 text-white' : 'bg-gray-200 dark:bg-gray-600'}`}>Bar Chart</button>
                 <button onClick={() => setChartType('pie')} className={`px-4 py-2 text-sm font-medium rounded-md ${chartType === 'pie' ? 'bg-blue-500 text-white' : 'bg-gray-200 dark:bg-gray-600'}`}>Pie Chart</button>
            </div>
            <div className="w-full h-96">
                {chartType === 'bar' ? <BarChartComponent data={data} /> : <PieChartComponent data={data} />}
            </div>
        </div>
    );
}

const TableView: React.FC<{ result: QueryResult }> = ({ result }) => {
    if (!result.rows || result.rows.length === 0) {
        return <div className="text-center p-8 text-gray-500">The query returned no results.</div>
    }

    return (
        <div className="w-full h-full overflow-auto">
            <table className="min-w-max border-collapse divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700 sticky top-0 z-10">
                    <tr>
                        {result.columns.map(col => (
                            <th
                                key={col}
                                scope="col"
                                className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider whitespace-nowrap"
                            >
                                {col}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {result.rows.map((row, i) => (
                        <tr key={i}>
                            {result.columns.map(col => (
                                <td
                                    key={col}
                                    className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100"
                                >
                                    {String(row[col])}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};



export const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ result, isLoading, error, chartData }) => {
    const [view, setView] = useState<ViewMode>(ViewMode.Table);

    const renderContent = () => {
        if (isLoading) {
            return <div className="flex flex-col items-center justify-center h-full"><Spinner /> <p className="mt-4">Running query...</p></div>;
        }
        if (error) {
            return <div className="text-center p-8 text-red-500 bg-red-50 dark:bg-red-900/20 rounded-lg">{error}</div>;
        }
        if (!result) {
            return <div className="text-center p-8 text-gray-500">Results will be displayed here.</div>;
        }

        return (
            <>
                {view === ViewMode.Table ? <TableView result={result} /> : <ChartView data={chartData} />}
            </>
        )
    }

    return (
        <div className="flex-1 bg-white dark:bg-gray-800 p-4 rounded-lg shadow-md flex flex-col min-h-0">
             <div className="flex items-center justify-between mb-4 border-b border-gray-200 dark:border-gray-700 pb-2 flex-shrink-0">
                <div className="flex items-center gap-4">
                    <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-200">Results</h2>
                    {result && !error && result.execution_time_ms !== undefined && (
                        <div className="flex items-center gap-2 text-sm">
                            <span className="text-gray-500 dark:text-gray-400">Execution time:</span>
                            <span className="font-mono font-semibold text-blue-600 dark:text-blue-400">
                                {result.execution_time_ms < 1000 
                                    ? `${result.execution_time_ms} ms`
                                    : `${(result.execution_time_ms / 1000).toFixed(2)} s`
                                }
                            </span>
                        </div>
                    )}
                </div>
                {result && !error && (
                    <div className="flex items-center space-x-2">
                        <button onClick={() => setView(ViewMode.Table)} className={`p-2 rounded-md ${view === ViewMode.Table ? 'bg-blue-100 dark:bg-blue-900' : 'hover:bg-gray-100 dark:hover:bg-gray-700'}`} title="Table View"><IconTable className="h-5 w-5 text-blue-500" /></button>
                        <button onClick={() => setView(ViewMode.Chart)} className={`p-2 rounded-md ${view === ViewMode.Chart ? 'bg-blue-100 dark:bg-blue-900' : 'hover:bg-gray-100 dark:hover:bg-gray-700'}`} title="Chart View"><IconChartBar className="h-5 w-5 text-blue-500" /></button>
                    </div>
                )}
            </div>
            <div className="flex-1 overflow-auto">
              {renderContent()}
            </div>
             {/* {result && !error && (
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 flex-shrink-0">
                    <h3 className="text-sm font-semibold flex items-center text-gray-600 dark:text-gray-300"><IconCode className="h-4 w-4 mr-2" /> Executed Query</h3>
                    <pre className="text-xs bg-gray-100 dark:bg-gray-900 p-2 rounded-md mt-2 overflow-auto text-gray-500 dark:text-gray-400"><code>{result.query}</code></pre>
                </div>
            )} */}
        </div>
    );
};
