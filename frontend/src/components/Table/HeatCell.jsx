import React from 'react';
import { formatHeat } from '../../utils/formatters';

/**
 * Premium heat cell with value and percentage indicator
 */
const HeatCell = ({ value, heat, unit = '', suffix = '' }) => {
    const { formatted: heatFormatted, colorClass } = formatHeat(heat);

    return (
        <div className="flex flex-col gap-0.5">
            <span className="heat-value">
                {value}{suffix}{unit}
            </span>
            <span className={`heat-percent ${colorClass}`}>
                {heatFormatted}
            </span>
        </div>
    );
};

export default HeatCell;
