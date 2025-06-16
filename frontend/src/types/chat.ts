/* eslint-disable @typescript-eslint/no-explicit-any */
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  data?: AnalysisData;
  charts?: ChartData[];
  workflow_id?: string;
  loading?: boolean;
}

export interface AnalysisData {
  consolidated_metrics?: {
    total_items?: number;
    total_value?: number;
    critical_stock_count?: number;
    low_stock_count?: number;
    total_revenue?: number;
    total_orders?: number;
    average_order_value?: number;
    unique_customers?: number;
    revenue_per_customer?: number;
    customer_segments?: Record<string, number>;
    [key: string]: any;
  };
  executive_summary?: {
    overview?: string;
    key_metrics?: Record<string, any>;
    performance_highlights?: string[];
    critical_actions?: string[];
  };
  recommendations?: Recommendation[];
  charts?: ChartData[];
  step_summaries?: Record<string, any>;
  [key: string]: any;
}

export interface Recommendation {
  type: string;
  product_sku?: string;
  current_quantity?: number;
  recommended_quantity?: number;
  priority: 'high' | 'medium' | 'low';
  reason: string;
  estimated_cost?: number;
}

export interface ChartData {
  type: string;
  title: string;
  chart_data: any;
  summary?: Record<string, any>;
}

export interface ChatRequest {
  message: string;
  context?: Record<string, any>;
}

export interface ChatResponse {
  response: string;
  data?: AnalysisData;
  charts?: ChartData[];
  workflow_id?: string;
}

export interface AnalysisRequest {
  analysis_type: 'inventory' | 'sales' | 'business';
  data_size?: 'small' | 'medium' | 'large';
  include_charts?: boolean;
}

export interface WorkflowInfo {
  type: string;
  name: string;
  description: string;
}

export interface ApiStatus {
  status: string;
  timestamp: string;
  orchestrator_status: string;
  available_agents: string[];
  api_version: string;
}
