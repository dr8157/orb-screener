import { useState, useEffect, useCallback, useRef } from 'react';
import { API_ENDPOINTS } from '../utils/constants';

/**
 * Parse signal data from WebSocket/API
 */
const parseSignal = (signal, idx) => ({
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
    decelPercent: parseFloat(signal.decel_percent) || 0,
    ignitionScore: parseFloat(signal.ignition_score) || 0,
    continuationScore: parseFloat(signal.continuation_score) || 0,
    qualityScore: parseFloat(signal.quality_score) || 0,
    score: parseInt(signal.score) || 0,
    state: signal.state || 'IDLE',
    sparkline: Array.isArray(signal.sparkline) ? signal.sparkline : [],
    yesterdayClose: parseFloat(signal.yesterday_close) || 0,
    lastUpdated: signal.last_updated ? new Date(signal.last_updated) : new Date(),
});

/**
 * Custom hook for WebSocket connection to ORB backend
 * @param {number} pollInterval - Polling interval in milliseconds (default 5000)
 */
export const useWebSocket = (pollInterval = 5000) => {
    const [signals, setSignals] = useState([]);
    const [isConnected, setIsConnected] = useState(false);
    const [isConnecting, setIsConnecting] = useState(true);
    const [error, setError] = useState(null);
    const [lastUpdate, setLastUpdate] = useState(null);

    const wsRef = useRef(null);
    const pollingIntervalRef = useRef(null);
    const isUnmounted = useRef(false);
    const pollIntervalRef = useRef(pollInterval);

    // Update poll interval ref when it changes
    useEffect(() => {
        pollIntervalRef.current = pollInterval;
    }, [pollInterval]);

    // Check if backend is reachable
    const checkBackend = useCallback(async () => {
        try {
            const response = await fetch(API_ENDPOINTS.health, {
                method: 'GET',
                signal: AbortSignal.timeout(2000)
            });
            return response.ok;
        } catch {
            return false;
        }
    }, []);

    // Fetch signals via HTTP
    const fetchSignalsHttp = useCallback(async () => {
        try {
            const response = await fetch(API_ENDPOINTS.topSignals, {
                signal: AbortSignal.timeout(3000)
            });

            if (response.ok) {
                const data = await response.json();
                if (data.signals && Array.isArray(data.signals)) {
                    const parsedSignals = data.signals.map((signal, idx) =>
                        parseSignal(signal, idx)
                    );
                    setSignals(parsedSignals);
                    setLastUpdate(new Date());
                    setIsConnected(true);
                    setIsConnecting(false);
                    setError(null);
                    return true;
                }
            }
            return false;
        } catch (err) {
            console.log('HTTP fetch error:', err.message);
            return false;
        }
    }, []);

    // Start HTTP polling
    const startPolling = useCallback(() => {
        if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
        }

        console.log(`🔄 Starting HTTP polling (interval: ${pollIntervalRef.current}ms)...`);

        // Immediate first fetch
        fetchSignalsHttp();

        // Then poll at the specified interval
        pollingIntervalRef.current = setInterval(async () => {
            const success = await fetchSignalsHttp();
            if (!success) {
                const backendUp = await checkBackend();
                if (backendUp) {
                    setIsConnected(true);
                    setError('Waiting for signals...');
                } else {
                    setIsConnected(false);
                    setError('Backend not responding');
                }
            }
        }, pollIntervalRef.current);
    }, [fetchSignalsHttp, checkBackend]);

    // Stop polling
    const stopPolling = useCallback(() => {
        if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
        }
    }, []);

    // Connect WebSocket (optional enhancement)
    const connectWebSocket = useCallback(() => {
        if (isUnmounted.current) return;
        if (wsRef.current?.readyState === WebSocket.OPEN) return;

        try {
            const ws = new WebSocket(API_ENDPOINTS.wsStream);

            ws.onopen = () => {
                console.log('✅ WebSocket connected');
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'update' && Array.isArray(data.signals)) {
                        const parsedSignals = data.signals.map((signal, idx) =>
                            parseSignal(signal, idx)
                        );
                        setSignals(parsedSignals);
                        setLastUpdate(new Date(data.timestamp || Date.now()));
                        setIsConnected(true);
                        setIsConnecting(false);
                    }
                } catch (e) {
                    // Ignore parse errors
                }
            };

            ws.onclose = () => {
                wsRef.current = null;
            };

            ws.onerror = () => {
                // WebSocket error, polling will continue
            };

            wsRef.current = ws;
        } catch {
            // WebSocket creation failed
        }
    }, []);

    // Manual reconnect
    const reconnect = useCallback(async () => {
        console.log('🔄 Manual reconnect...');
        setIsConnecting(true);
        setError(null);

        const backendUp = await checkBackend();

        if (backendUp) {
            setIsConnected(true);
            setIsConnecting(false);
            await fetchSignalsHttp();
            startPolling();
        } else {
            setIsConnected(false);
            setIsConnecting(false);
            setError('Backend not responding');
        }
    }, [checkBackend, fetchSignalsHttp, startPolling]);

    // Disconnect
    const disconnect = useCallback(() => {
        stopPolling();
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        setIsConnected(false);
    }, [stopPolling]);

    // Initialize on mount - fast startup
    useEffect(() => {
        isUnmounted.current = false;

        // Start immediately - fetch data first, don't wait for health check
        const init = async () => {
            setIsConnecting(true);

            // Try to fetch signals immediately (faster than health check first)
            const gotData = await fetchSignalsHttp();

            if (gotData) {
                // Data received - we're connected!
                setIsConnected(true);
                setIsConnecting(false);
                startPolling();
                connectWebSocket();
            } else {
                // No data - check if backend is up
                const backendUp = await checkBackend();
                if (backendUp) {
                    setIsConnected(true);
                    setIsConnecting(false);
                    setError('Waiting for data...');
                } else {
                    setIsConnected(false);
                    setIsConnecting(false);
                    setError('Backend not responding');
                }
                // Start polling anyway to keep trying
                startPolling();
            }
        };

        init();

        return () => {
            isUnmounted.current = true;
            disconnect();
        };
    }, []);

    // Restart polling when interval changes
    useEffect(() => {
        if (isConnected) {
            console.log(`⏱️ Polling interval changed to ${pollInterval}ms`);
            startPolling();
        }
    }, [pollInterval]);

    return {
        signals,
        isConnected,
        isConnecting,
        error,
        lastUpdate,
        reconnect,
        disconnect,
    };
};

export default useWebSocket;
