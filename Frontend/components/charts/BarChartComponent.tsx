
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { ChartData } from '../../types';

interface BarChartProps {
    data: ChartData[];
}

export const BarChartComponent: React.FC<BarChartProps> = ({ data }) => {
    return (
        <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(128, 128, 128, 0.2)" />
                <XAxis dataKey="name" stroke="rgb(156 163 175)" />
                <YAxis stroke="rgb(156 163 175)" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(31, 41, 55, 0.9)', 
                    borderColor: 'rgba(75, 85, 99, 1)',
                    color: '#fff'
                  }} 
                />
                <Legend />
                <Bar dataKey="value" fill="#3b82f6" />
            </BarChart>
        </ResponsiveContainer>
    );
};
