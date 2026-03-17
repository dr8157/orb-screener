import { useState, useEffect, useCallback } from 'react';
import { API_ENDPOINTS, DEFAULT_CONFIG } from '../utils/constants';

/**
 * Hook for managing configuration
 */
export const useConfig = () => {
    const [config, setConfig] = useState(DEFAULT_CONFIG);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    // Fetch config from backend
    const fetchConfig = useCallback(async () => {
        setIsLoading(true);
        try {
            const response = await fetch(API_ENDPOINTS.config);
            if (response.ok) {
                const data = await response.json();
                setConfig(data);
                setError(null);
            }
        } catch (err) {
            console.error('Failed to fetch config:', err);
            setError('Failed to load configuration');
        } finally {
            setIsLoading(false);
        }
    }, []);

    // Update config on backend
    const updateConfig = useCallback(async (newConfig) => {
        setIsLoading(true);
        try {
            const response = await fetch(API_ENDPOINTS.config, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newConfig),
            });

            if (response.ok) {
                const data = await response.json();
                setConfig(data.config || newConfig);
                setError(null);
                return true;
            }
            return false;
        } catch (err) {
            console.error('Failed to update config:', err);
            setError('Failed to save configuration');
            return false;
        } finally {
            setIsLoading(false);
        }
    }, []);

    // Reset to defaults
    const resetConfig = useCallback(async () => {
        return updateConfig(DEFAULT_CONFIG);
    }, [updateConfig]);

    // Fetch on mount
    useEffect(() => {
        fetchConfig();
    }, [fetchConfig]);

    return {
        config,
        isLoading,
        error,
        fetchConfig,
        updateConfig,
        resetConfig,
    };
};

export default useConfig;
