import { defineStore } from 'pinia'
import type { ApiDcfValuationResponse } from '../../../shared-types/src/index'

export interface ValuationHistoryRecord {
    id: string // Unique ID for the record
    timestamp: number // When the valuation was performed
    valuationResult: ApiDcfValuationResponse
}

export interface HistoryState {
    records: ValuationHistoryRecord[]
}

const HISTORY_STORAGE_KEY = 'valuation_history'
const MAX_HISTORY_RECORDS = 50 // Limit the number of records to prevent localStorage overflow

export const useHistoryStore = defineStore('history', {
    state: (): HistoryState => ({
        records: []
    }),
    actions: {
        /**
         * Add a valuation result to history
         */
        addRecord(result: ApiDcfValuationResponse) {
            if (!result || !result.stock_info) return

            // Create a new record with a unique ID
            const newRecord: ValuationHistoryRecord = {
                id: `${Date.now()}-${result.stock_info.ts_code}`,
                timestamp: Date.now(),
                valuationResult: result
            }

            // Add to the beginning of the array (newest first)
            this.records.unshift(newRecord)

            // Limit the number of records
            if (this.records.length > MAX_HISTORY_RECORDS) {
                this.records = this.records.slice(0, MAX_HISTORY_RECORDS)
            }

            // Save to localStorage
            this.saveToLocalStorage()
        },

        /**
         * Remove a record from history by ID
         */
        removeRecord(id: string) {
            this.records = this.records.filter(record => record.id !== id)
            this.saveToLocalStorage()
        },

        /**
         * Clear all history records
         */
        clearAllRecords() {
            this.records = []
            this.saveToLocalStorage()
        },

        /**
         * Save history to localStorage
         */
        saveToLocalStorage() {
            try {
                localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(this.records))
            } catch (error) {
                console.error('Failed to save valuation history to localStorage:', error)
            }
        },

        /**
         * Load history from localStorage
         */
        loadFromLocalStorage() {
            try {
                const storedHistory = localStorage.getItem(HISTORY_STORAGE_KEY)
                if (storedHistory) {
                    this.records = JSON.parse(storedHistory)
                }
            } catch (error) {
                console.error('Failed to load valuation history from localStorage:', error)
            }
        }
    },
    getters: {
        /**
         * Get all history records
         */
        getAllRecords: (state) => state.records,
        
        /**
         * Get a record by ID
         */
        getRecordById: (state) => (id: string) => {
            return state.records.find(record => record.id === id)
        }
    }
})
