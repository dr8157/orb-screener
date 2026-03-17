/**
 * Format price with Indian Rupee symbol
 * @param {number} price - Price value
 * @returns {string} Formatted price string
 */
export const formatPrice = (price) => {
    if (!price && price !== 0) return '₹0.00';
    return `₹${parseFloat(price).toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    })}`;
};

/**
 * Format percentage with sign
 * @param {number} percent - Percentage value
 * @returns {string} Formatted percentage string
 */
export const formatPercent = (percent) => {
    if (!percent && percent !== 0) return '0.00%';
    const sign = percent >= 0 ? '+' : '';
    return `${sign}${parseFloat(percent).toFixed(2)}%`;
};

/**
 * Format volume in Lakhs/Crores
 * @param {number} volume - Volume value
 * @returns {string} Formatted volume string
 */
export const formatVolume = (volume) => {
    if (!volume) return '0L';
    if (volume >= 1e7) {
        return `${(volume / 1e7).toFixed(2)}Cr`;
    }
    return `${(volume / 1e5).toFixed(2)}L`;
};

/**
 * Format value in Crores
 * @param {number} value - Value in crores
 * @returns {string} Formatted value string
 */
export const formatValue = (value) => {
    if (!value && value !== 0) return '0.00Cr';
    return `${parseFloat(value).toFixed(2)}Cr`;
};

/**
 * Format heat percentage with color class
 * @param {number} heat - Heat percentage
 * @returns {object} Formatted heat and CSS class
 */
export const formatHeat = (heat) => {
    const value = parseFloat(heat) || 0;
    let colorClass = 'heat-low';

    if (value >= 1000) {
        colorClass = 'heat-extreme';
    } else if (value >= 500) {
        colorClass = 'heat-high';
    } else if (value >= 100) {
        colorClass = 'heat-medium';
    } else if (value < 0) {
        colorClass = 'heat-negative';
    }

    const sign = value >= 0 ? '+' : '';
    const formatted = `${sign}${value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}%`;

    return { formatted, colorClass };
};

/**
 * Format time in HH:MM:SS
 * @param {Date} date - Date object
 * @returns {string} Formatted time string
 */
export const formatTime = (date) => {
    if (!date) return '--:--:--';
    return date.toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
    });
};

/**
 * Format time in HH:MM
 * @param {Date} date - Date object
 * @returns {string} Formatted time string
 */
export const formatTimeShort = (date) => {
    if (!date) return '--:--';
    return date.toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
    });
};

/**
 * Get score class based on score value
 * @param {number} score - Score value (0-100)
 * @returns {string} CSS class name
 */
export const getScoreClass = (score) => {
    if (score >= 90) return 'score-excellent';
    if (score >= 80) return 'score-good';
    if (score >= 70) return 'score-average';
    return 'score-low';
};

/**
 * Parse signal data from WebSocket
 * @param {object} signal - Raw signal from backend
 * @param {number} idx - Index for fallback rank
 * @returns {object} Parsed signal object
 */
export const parseSignal = (signal, idx) => ({
    rank: signal.rank || idx + 1,
    symbol: signal.symbol || '',
    time: signal.time || '--:--',
    dir: signal.dir || 'LONG',
    price: parseFloat(signal.price) || 0,
    changePercent: parseFloat(signal.change_percent) || 0,
    volume: signal.volume || '0L',
    volumeRaw: signal.volume_raw || 0,
    volumeHeat: parseFloat(signal.volume_heat_percent) || 0,
    dayVolume: signal.day_volume || '0L',
    dayVolumeRaw: signal.day_volume_raw || 0,
    value: parseFloat(signal.value) || 0,
    valueHeat: parseFloat(signal.value_heat_percent) || 0,
    body: parseFloat(signal.body) || 0,
    bodyHeat: parseFloat(signal.body_heat_percent) || 0,
    orbValid: signal.orb_valid || false,
    orbHigh: parseFloat(signal.orb_high) || 0,
    orbLow: parseFloat(signal.orb_low) || 0,
    speedMinutes: parseInt(signal.speed_minutes) || 0,
    pullbackPercent: parseFloat(signal.pullback_percent) || 0,
    decelOk: signal.decel_ok || false,
    ignitionScore: parseFloat(signal.ignition_score) || 0,
    continuationScore: parseFloat(signal.continuation_score) || 0,
    qualityScore: parseFloat(signal.quality_score) || 0,
    score: parseInt(signal.score) || 0,
    state: signal.state || 'IDLE',
    sparkline: Array.isArray(signal.sparkline) ? signal.sparkline : [],
    yesterdayClose: parseFloat(signal.yesterday_close) || 0,
    lastUpdated: signal.last_updated ? new Date(signal.last_updated) : new Date(),
});
