/**
 * API Configuration
 */

// ============================================
// LOCAL DEVELOPMENT (default)
// ============================================
// const BACKEND_URL = 'http://localhost:8000';
// export const API_BASE_URL = BACKEND_URL;
// export const WS_BASE_URL = BACKEND_URL.replace('http', 'ws');

// ============================================
// NGROK MODE / PRODUCTION - Uncomment below & comment above
// ============================================
const BACKEND_URL = import.meta.env.VITE_API_URL || '';
const WS_PROTOCOL = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
export const API_BASE_URL = BACKEND_URL;
export const WS_BASE_URL = BACKEND_URL ? BACKEND_URL.replace(/^http/, 'ws') : `${WS_PROTOCOL}//${window.location.host}`;


// end


export const API_ENDPOINTS = {
    health: `${API_BASE_URL}/`,
    config: `${API_BASE_URL}/api/config`,
    topSignals: `${API_BASE_URL}/api/top-signals`,
    debug: `${API_BASE_URL}/api/debug`,
    baselineRefresh: `${API_BASE_URL}/api/baseline/refresh`,
    wsStream: `${WS_BASE_URL}/ws/stream`,
};

// Default configuration
export const DEFAULT_CONFIG = {
    // Baseline Settings
    baseline_days: 20,

    // Threshold Settings
    volume_multiplier: 5.0,
    value_threshold: 4.0,
    body_threshold: 1.5,
    score_threshold: 70,
    top_n_display: 10,
    watchlist: [],  // Required by backend

    // Score Weights (must sum to 1.0 / 100%)
    weight_volume: 0.25,
    weight_value: 0.25,
    weight_body: 0.2,
    weight_speed: 0.15,
    weight_pullback: 0.1,
    weight_decel: 0.05,

    // Scoring Formula Constants
    heat_max: 1000,        // Cap heat% at this value for normalization
    speed_decay_k: 30,     // Speed decay constant (at k minutes, factor ≈ 0.37)
    pb_max: 5.0,           // Max pullback% for normalization
};

// Score thresholds
export const SCORE_THRESHOLDS = {
    excellent: 90,
    good: 80,
    average: 70,
};

// Heat thresholds
export const HEAT_THRESHOLDS = {
    extreme: 1000,
    high: 500,
    medium: 100,
};
