import React, { useMemo } from 'react';

/**
 * Premium SVG Sparkline with glow and gradient effects
 */
const Sparkline = ({
    data = [],
    isPositive = true,
    width = 100,
    height = 36,
    strokeWidth = 2,
}) => {
    const filterId = useMemo(() => `spark-${Math.random().toString(36).substr(2, 9)}`, []);
    const gradientId = useMemo(() => `grad-${Math.random().toString(36).substr(2, 9)}`, []);

    const { points, areaPoints, lastY, trend } = useMemo(() => {
        if (!data || !Array.isArray(data) || data.length < 2) {
            return { points: '', areaPoints: '', lastY: height / 2, trend: 0 };
        }

        const validData = data.filter(v => typeof v === 'number' && !isNaN(v) && isFinite(v));
        if (validData.length < 2) {
            return { points: '', areaPoints: '', lastY: height / 2, trend: 0 };
        }

        const max = Math.max(...validData);
        const min = Math.min(...validData);
        const range = max - min || 1;
        const padding = 4;

        const pointsArray = validData.map((value, index) => {
            const x = (index / (validData.length - 1)) * (width - padding * 2) + padding;
            const y = (height - padding) - ((value - min) / range) * (height - padding * 2);
            return { x, y };
        });

        const pointsStr = pointsArray.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
        const lastPoint = pointsArray[pointsArray.length - 1];

        // Area path for gradient fill
        const areaStr = `M ${padding},${height - padding} ` +
            pointsArray.map((p, i) => `${i === 0 ? 'L' : ''} ${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ') +
            ` L ${width - padding},${height - padding} Z`;

        // Calculate trend
        const firstVal = validData[0];
        const lastVal = validData[validData.length - 1];
        const trendVal = ((lastVal - firstVal) / firstVal) * 100;

        return {
            points: pointsStr,
            areaPoints: areaStr,
            lastY: lastPoint?.y || height / 2,
            trend: trendVal
        };
    }, [data, width, height]);

    // Empty state
    if (!points) {
        return (
            <svg width={width} height={height} className="opacity-30">
                <line
                    x1="4"
                    y1={height / 2}
                    x2={width - 4}
                    y2={height / 2}
                    stroke="#404040"
                    strokeWidth="1"
                    strokeDasharray="4,4"
                />
            </svg>
        );
    }

    const mainColor = isPositive ? '#00ff88' : '#ff4757';
    const dimColor = isPositive ? '#00cc6a' : '#cc3944';

    return (
        <svg width={width} height={height} className="overflow-visible">
            <defs>
                {/* Glow filter */}
                <filter id={filterId} x="-50%" y="-50%" width="200%" height="200%">
                    <feGaussianBlur stdDeviation="2" result="blur" />
                    <feMerge>
                        <feMergeNode in="blur" />
                        <feMergeNode in="SourceGraphic" />
                    </feMerge>
                </filter>

                {/* Gradient fill */}
                <linearGradient id={gradientId} x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor={mainColor} stopOpacity="0.3" />
                    <stop offset="100%" stopColor={mainColor} stopOpacity="0" />
                </linearGradient>
            </defs>

            {/* Area fill */}
            <path
                d={areaPoints}
                fill={`url(#${gradientId})`}
            />

            {/* Main line */}
            <polyline
                points={points}
                fill="none"
                stroke={mainColor}
                strokeWidth={strokeWidth}
                strokeLinecap="round"
                strokeLinejoin="round"
                filter={`url(#${filterId})`}
            />

            {/* End point */}
            <circle
                cx={width - 4}
                cy={lastY}
                r="4"
                fill={mainColor}
                className="animate-pulse"
            />
            <circle
                cx={width - 4}
                cy={lastY}
                r="2"
                fill="#ffffff"
            />
        </svg>
    );
};

export default Sparkline;
