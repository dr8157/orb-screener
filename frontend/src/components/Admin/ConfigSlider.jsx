import React from 'react';

/**
 * Premium configuration slider component
 */
const ConfigSlider = ({
    label,
    value,
    min,
    max,
    step,
    suffix = '',
    onChange,
}) => {
    const percentage = ((value - min) / (max - min)) * 100;

    return (
        <div className="config-slider">
            <div className="flex items-center justify-between mb-2">
                <label className="text-sm text-gray-400">{label}</label>
                <span className="text-sm font-mono font-semibold text-white">
                    {typeof value === 'number' ? value.toFixed(step < 1 ? 2 : 0) : value}{suffix}
                </span>
            </div>
            <div className="relative">
                <div
                    className="absolute top-1/2 left-0 h-1.5 rounded-full bg-gradient-to-r from-[#00ff88] to-[#00cc6a] -translate-y-1/2 pointer-events-none"
                    style={{ width: `${percentage}%` }}
                />
                <input
                    type="range"
                    min={min}
                    max={max}
                    step={step}
                    value={value}
                    onChange={(e) => onChange?.(parseFloat(e.target.value))}
                    className="w-full h-1.5 bg-gray-800 rounded-full appearance-none cursor-pointer relative z-10"
                    style={{
                        background: `linear-gradient(to right, transparent ${percentage}%, rgba(55, 65, 81, 1) ${percentage}%)`
                    }}
                />
            </div>
            <div className="flex justify-between mt-1 text-xs text-gray-600">
                <span>{min}{suffix}</span>
                <span>{max}{suffix}</span>
            </div>
        </div>
    );
};

export default ConfigSlider;
