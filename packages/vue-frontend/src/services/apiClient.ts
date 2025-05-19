// apiClient.ts

const API_BASE_URL = 'http://localhost:8125/api/v1'; // 从后端 FastAPI 服务获取

interface ApiErrorData {
    detail?: string | { msg: string; type: string }[];
}

class ApiClientError extends Error {
    status: number;
    data: ApiErrorData;

    constructor(message: string, status: number, data: ApiErrorData) {
        super(message);
        this.name = 'ApiClientError';
        this.status = status;
        this.data = data;
    }
}

async function request<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const config: RequestInit = {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
    };

    try {
        const response = await fetch(url, config);

        if (!response.ok) {
            let errorData: ApiErrorData = {};
            try {
                errorData = await response.json();
            } catch (e) {
                // If response is not JSON, use status text
                errorData = { detail: response.statusText };
            }
            throw new ApiClientError(
                `API request failed with status ${response.status}`,
                response.status,
                errorData
            );
        }

        // Handle cases where response might be empty (e.g., 204 No Content)
        if (response.status === 204) {
            return undefined as T; // Or handle as appropriate for your app
        }

        return (await response.json()) as T;
    } catch (error) {
        if (error instanceof ApiClientError) {
            throw error;
        }
        // Network errors or other fetch-related issues
        console.error('API Client Network Error:', error);
        throw new Error('Network error or API is unreachable.');
    }
}

export const apiClient = {
    get: <T>(endpoint: string, options?: RequestInit) =>
        request<T>(endpoint, { ...options, method: 'GET' }),

    post: <T, U>(endpoint: string, body: U, options?: RequestInit) =>
        request<T>(endpoint, { ...options, method: 'POST', body: JSON.stringify(body) }),

    put: <T, U>(endpoint: string, body: U, options?: RequestInit) =>
        request<T>(endpoint, { ...options, method: 'PUT', body: JSON.stringify(body) }),

    delete: <T>(endpoint: string, options?: RequestInit) =>
        request<T>(endpoint, { ...options, method: 'DELETE' }),

    // TODO: Add other methods like patch if needed
};

// --- Specific API functions ---

// Import shared types for better type safety
import type {
    ApiDcfValuationRequest, // Assuming this is defined for valuation
    ApiDcfValuationResponse // Assuming this is defined for valuation
    ,

    ApiStockScreenerRequest,
    ApiStockScreenerResponse,
    ApiUpdateScreenerDataRequest,
    ApiUpdateScreenerDataResponse
} from '@shared-types/index';


export const screenerApi = {
    getScreenedStocks: (params: ApiStockScreenerRequest): Promise<ApiStockScreenerResponse> => {
        return apiClient.post<ApiStockScreenerResponse, ApiStockScreenerRequest>('/screener/stocks', params);
    },
    updateScreenerData: (params: ApiUpdateScreenerDataRequest): Promise<ApiUpdateScreenerDataResponse> => {
        return apiClient.post<ApiUpdateScreenerDataResponse, ApiUpdateScreenerDataRequest>('/screener/update-data', params);
    }
};

export const valuationApi = {
    performDcfValuation: async (params: ApiDcfValuationRequest): Promise<ApiDcfValuationResponse> => {
        // Ensure the endpoint matches your FastAPI valuation endpoint, e.g., /valuation
        console.log('发送估值请求，敏感性分析参数:', params.sensitivity_analysis);
        try {
            const response = await apiClient.post<ApiDcfValuationResponse, ApiDcfValuationRequest>('/valuation', params);
            console.log('估值响应中的敏感性分析结果:', response.valuation_results?.sensitivity_analysis_result);
            return response;
        } catch (error) {
            console.error('估值请求失败:', error);
            throw error;
        }
    }
};


// Example usage (can be removed or moved to actual service files):
/*
interface StockValuationRequest {
  stock_code: string;
  // ... other properties
}

interface ValuationResult {
  // ... result properties
}

async function getValuation(payload: StockValuationRequest): Promise<ValuationResult> {
  try {
    const result = await apiClient.post<ValuationResult, StockValuationRequest>('/valuation', payload);
    console.log('Valuation result:', result);
    return result;
  } catch (error) {
    if (error instanceof ApiClientError) {
      console.error('API Error:', error.status, error.message, error.data);
    } else {
      console.error('Generic Error:', error);
    }
    throw error;
  }
}
*/

export { ApiClientError };
