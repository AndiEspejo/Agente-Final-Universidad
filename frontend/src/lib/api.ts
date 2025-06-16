import {
  ChatRequest,
  ChatResponse,
  AnalysisRequest,
  WorkflowInfo,
  ApiStatus,
} from '@/types/chat';
import Cookies from 'js-cookie';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private getAuthHeaders(): Record<string, string> {
    const token = Cookies.get('auth_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeaders(),
        ...options.headers,
      },
    };

    const response = await fetch(url, { ...defaultOptions, ...options });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));

      // Handle authentication errors
      if (response.status === 401) {
        // Token expired or invalid, redirect to auth
        window.location.href = '/auth';
        throw new Error(
          'Sesión expirada. Por favor, inicia sesión nuevamente.'
        );
      }

      throw new Error(
        errorData.detail || `HTTP error! status: ${response.status}`
      );
    }

    return response.json();
  }

  async sendChatMessage(message: ChatRequest): Promise<ChatResponse> {
    return this.request<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify(message),
    });
  }

  async runAnalysis(request: AnalysisRequest): Promise<unknown> {
    return this.request('/analyze', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getWorkflows(): Promise<{ available_workflows: WorkflowInfo[] }> {
    return this.request('/workflows');
  }

  async getStatus(): Promise<ApiStatus> {
    return this.request('/status');
  }

  async healthCheck(): Promise<boolean> {
    try {
      const status = await this.getStatus();
      return status.status === 'healthy';
    } catch {
      return false;
    }
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export bound methods to avoid 'this' context issues
export const sendChatMessage = apiClient.sendChatMessage.bind(apiClient);
export const runAnalysis = apiClient.runAnalysis.bind(apiClient);
export const getWorkflows = apiClient.getWorkflows.bind(apiClient);
export const getStatus = apiClient.getStatus.bind(apiClient);
export const healthCheck = apiClient.healthCheck.bind(apiClient);
