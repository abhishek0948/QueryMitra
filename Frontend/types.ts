export interface DataSet {
  id: string;
  name: string;
  description: string;
  schema: Record<string, 'string' | 'number' | 'boolean'>;
}

export type QueryResult = {
  columns: string[];
  rows: Record<string, string | number>[];
  query: string;
};

export enum QueryMode {
  NL = 'Natural Language',
  SQL = 'SQL',
  MongoDB = 'MongoDB'
}

export enum ViewMode {
  Table = 'Table',
  Chart = 'Chart',
}

export interface ChartData {
    name: string;
    value: number;
}
