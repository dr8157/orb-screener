import React from 'react';
import { Wifi, WifiOff, Loader2, RefreshCw } from 'lucide-react';

/**
 * Live connection status indicator with premium styling
 */
const LiveIndicator = ({ isConnected, isConnecting, error, onReconnect }) => {
    if (isConnecting) {
        return (
            <div className="live-indicator connecting">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Connecting...</span>
            </div>
        );
    }

    if (!isConnected) {
        return (
            <button
                onClick={onReconnect}
                className="live-indicator offline group cursor-pointer hover:bg-[#ff4757]/20 transition-all"
            >
                <WifiOff className="w-4 h-4" />
                <span>Offline</span>
                <RefreshCw className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
            </button>
        );
    }

    return (
        <div className="live-indicator connected">
            <div className="live-dot" />
            <span>Live</span>
            <Wifi className="w-4 h-4 opacity-60" />
        </div>
    );
};

export default LiveIndicator;
