/**
 * 应用配置文件
 */

// API配置
export const API_CONFIG = {
    BASE_URL: process.env.VUE_APP_API_BASE_URL || 'http://localhost:8000',
    TIMEOUT: 30000,
    IMAGE_ANALYSIS_TIMEOUT: 60000
}// 上传配置
export const UPLOAD_CONFIG = {
    MAX_SIZE: 10 * 1024 * 1024, // 10MB
    ACCEPTED_TYPES: ['image/jpeg', 'image/png', 'image/gif'],
    ACCEPTED_EXTENSIONS: ['.jpg', '.jpeg', '.png', '.gif']
}

// 分析配置
export const ANALYSIS_CONFIG = {
    DEFAULT_CONFIDENCE_THRESHOLD: 0.5,
    DEFAULT_ANALYSIS_TYPE: 'full',
    PROGRESS_UPDATE_INTERVAL: 1000 // 1秒
}

// UI配置
export const UI_CONFIG = {
    ENTITY_TYPE_COLORS: {
        insect: '#f56c6c',
        tree: '#67c23a',
        disease_symptom: '#e6a23c',
        environment: '#409eff'
    },
    RISK_LEVEL_COLORS: {
        high: '#f56c6c',
        medium: '#e6a23c',
        low: '#67c23a'
    }
}

export default {
    API_CONFIG,
    UPLOAD_CONFIG,
    ANALYSIS_CONFIG,
    UI_CONFIG
}