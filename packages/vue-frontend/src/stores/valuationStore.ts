import { defineStore } from 'pinia'
import type { ApiDcfValuationResponse } from '../../../shared-types/src/index'; // 调整路径以匹配项目结构

export interface ValuationState {
    valuationResult: ApiDcfValuationResponse | null
    isLoading: boolean
    error: string | null
}

export const useValuationStore = defineStore('valuation', {
    state: (): ValuationState => ({
        valuationResult: null,
        isLoading: false,
        error: null
    }),
    actions: {
        setValuationResult(result: ApiDcfValuationResponse | null) {
            this.valuationResult = result
            this.isLoading = false
            this.error = null
        },
        setLoading(loading: boolean) {
            this.isLoading = loading
            if (loading) {
                this.error = null // Reset error when loading starts
            }
        },
        setError(errorMessage: string | null) {
            this.error = errorMessage
            this.isLoading = false
            // Potentially clear result on error, or let components decide
            // this.valuationResult = null; 
        },
        clearResult() {
            this.valuationResult = null
            this.isLoading = false
            this.error = null
        }
    },
    getters: {
        hasValuationResult: (state) => !!state.valuationResult,
        getValuationResult: (state) => state.valuationResult,
        getIsLoading: (state) => state.isLoading,
        getError: (state) => state.error
    }
})
