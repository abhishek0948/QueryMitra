
import type { DataSet } from './types';

export const MOCK_DATASETS: DataSet[] = [
    {
        id: 'plfs_2022_23',
        name: 'Periodic Labour Force Survey (PLFS) 2022-23',
        description: 'Annual report on employment and unemployment indicators in India.',
        schema: {
            "state": "string",
            "age": "number",
            "gender": "string",
            "employment_status": "string",
            "monthly_income": "number",
        }
    },
    {
        id: 'hces_2022_23',
        name: 'Household Consumer Expenditure Survey (HCES) 2022-23',
        description: 'Collects information on consumption spending patterns of households.',
        schema: {
            "state": "string",
            "household_size": "number",
            "monthly_expenditure_food": "number",
            "monthly_expenditure_nonfood": "number",
            "sector": "string"
        }
    }
];

export const MOCK_QUERY_RESULT = {
    'plfs_2022_23': {
        columns: ['state', 'average_income'],
        rows: [
            { state: 'Maharashtra', average_income: 25000 },
            { state: 'Karnataka', average_income: 22000 },
            { state: 'Tamil Nadu', average_income: 21500 },
            { state: 'Uttar Pradesh', average_income: 15000 },
            { state: 'West Bengal', average_income: 18000 },
        ],
        query: `db.plfs_2022_23.aggregate([...])`
    },
    'hces_2022_23': {
        columns: ['sector', 'avg_food_expenditure'],
        rows: [
            { sector: 'Urban', avg_food_expenditure: 8500 },
            { sector: 'Rural', avg_food_expenditure: 5500 },
        ],
        query: `db.hces_2022_23.aggregate([...])`
    }
};
