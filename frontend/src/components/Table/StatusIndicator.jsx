import React from 'react';
import { Check, X, Activity } from 'lucide-react';

/**
 * Premium status indicator with icons
 */
const StatusIndicator = ({ isValid, showWave = false }) => {
    if (isValid) {
        return (
            <div className="status-indicator valid">
                <Check className="w-4 h-4" strokeWidth={3} />
            </div>
        );
    }

    if (showWave) {
        return (
            <div className="status-indicator invalid">
                <Activity className="w-4 h-4" strokeWidth={2} />
            </div>
        );
    }

    return (
        <div className="status-indicator invalid">
            <X className="w-4 h-4" strokeWidth={2.5} />
        </div>
    );
};

export default StatusIndicator;
