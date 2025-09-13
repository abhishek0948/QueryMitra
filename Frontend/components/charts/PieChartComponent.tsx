
import React from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { ChartData } from '../../types';

interface PieChartProps {
    data: ChartData[];
}

const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#ef4444', '#f97316', '#eab308'];

export const PieChartComponent: React.FC<PieChartProps> = ({ data }) => {
    return (
        <ResponsiveContainer width="100%" height="100%">
            <PieChart>
                <Pie
                    data={data}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={120}
                    fill="#8884d8"
                    dataKey="value"
                    nameKey="name"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                    {data.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                </Pie>
                <Tooltip 
                    contentStyle={{ 
                        backgroundColor: 'rgba(31, 41, 55, 0.9)', 
                        borderColor: 'rgba(75, 85, 99, 1)',
                        color: '#fff'
                    }}
                />
                <Legend />
            </PieChart>
        </ResponsiveContainer>
    );
};
