import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

/**
 * Premium direction badge with icons and gradient styling
 */
const DirectionBadge = ({ direction }) => {
    const isLong = direction === 'LONG';

    return (
        <div className={`direction-badge ${isLong ? 'long' : 'short'}`}>
            {isLong ? (
                <TrendingUp className="w-3.5 h-3.5" strokeWidth={2.5} />
            ) : (
                <TrendingDown className="w-3.5 h-3.5" strokeWidth={2.5} />
            )}
            <span>{isLong ? 'Long' : 'Short'}</span>
        </div>
    );
};

export default DirectionBadge;
