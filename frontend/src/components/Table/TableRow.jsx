import React from 'react';
import DirectionBadge from './DirectionBadge';
import HeatCell from './HeatCell';
import Sparkline from './Sparkline';
import ScoreBadge from './ScoreBadge';
import StatusIndicator from './StatusIndicator';
import { formatPrice, formatPercent } from '../../utils/formatters';

/**
 * Premium table row with hover effects and animations
 */
const TableRow = ({ signal, isNew = false }) => {
    const {
        rank = 0,
        symbol = '',
        time = '--:--',
        dir = 'LONG',
        price = 0,
        changePercent = 0,
        volume = '0L',
        volumeHeat = 0,
        dayVolume = '0L',
        value = 0,
        valueHeat = 0,
        body = 0,
        bodyHeat = 0,
        orbValid = false,
        speedMinutes = 0,
        pullbackPercent = 0,
        decelOk = false,
        decelPercent = 0,
        score = 0,
        sparkline = [],
    } = signal || {};

    const isLong = dir === 'LONG';
    const isPositive = changePercent >= 0;

    return (
        <tr
            className={`group transition-all duration-300 ${isNew ? 'flash-breakout' : ''
                } ${score >= 90 ? 'bg-gradient-to-r from-[#00ff88]/5 to-transparent' : ''}`}
        >
            {/* Rank */}
            <td className="px-2 sm:px-3 md:px-5 py-2 sm:py-3 md:py-4">
                <span className="inline-flex items-center justify-center w-6 h-6 sm:w-7 sm:h-7 md:w-8 md:h-8 rounded-md sm:rounded-lg bg-black/30 text-gray-400 font-mono font-semibold text-xs sm:text-sm">
                    {rank}
                </span>
            </td>

            {/* Symbol */}
            <td className="px-2 sm:px-3 md:px-5 py-2 sm:py-3 md:py-4">
                <span className="ticker-symbol group-hover:text-[#00ff88] transition-colors">
                    {symbol}
                </span>
            </td>

            {/* Time */}
            <td className="px-2 sm:px-3 md:px-5 py-2 sm:py-3 md:py-4">
                <span className="text-gray-500 font-mono text-[10px] sm:text-xs">
                    {time}
                </span>
            </td>

            {/* Direction */}
            <td className="px-2 sm:px-3 md:px-5 py-2 sm:py-3 md:py-4">
                <DirectionBadge direction={dir} />
            </td>

            {/* Price */}
            <td className="px-2 sm:px-3 md:px-5 py-2 sm:py-3 md:py-4 text-right">
                <span className="price-display text-white">
                    {formatPrice(price)}
                </span>
            </td>

            {/* Change % */}
            <td className="px-2 sm:px-3 md:px-5 py-2 sm:py-3 md:py-4 text-right">
                <span className={`price-change ${isPositive ? 'positive' : 'negative'}`}>
                    {formatPercent(changePercent)}
                </span>
            </td>

            {/* ORB Volume */}
            <td className="px-2 sm:px-3 md:px-5 py-2 sm:py-3 md:py-4">
                <HeatCell value={volume} heat={volumeHeat} />
            </td>

            {/* Day Volume (Real-time) */}
            <td className="px-2 sm:px-3 md:px-5 py-2 sm:py-3 md:py-4">
                <span className="text-[10px] sm:text-xs md:text-sm text-cyan-400 font-mono font-medium">
                    {dayVolume}
                </span>
            </td>

            {/* Value */}
            <td className="px-2 sm:px-3 md:px-5 py-2 sm:py-3 md:py-4">
                <HeatCell
                    value={typeof value === 'number' ? value.toFixed(2) : value}
                    heat={valueHeat}
                    unit=" Cr"
                />
            </td>

            {/* Body */}
            <td className="px-2 sm:px-3 md:px-5 py-2 sm:py-3 md:py-4">
                <HeatCell
                    value={typeof body === 'number' ? body.toFixed(2) : body}
                    heat={bodyHeat}
                    suffix="x"
                />
            </td>

            {/* ORB */}
            <td className="px-2 sm:px-3 md:px-5 py-2 sm:py-3 md:py-4 text-center">
                <StatusIndicator isValid={orbValid} />
            </td>

            {/* Speed */}
            <td className="px-2 sm:px-3 md:px-5 py-2 sm:py-3 md:py-4 text-center">
                <span className={`font-mono text-[10px] sm:text-xs md:text-sm ${speedMinutes >= 0 && speedMinutes <= 15
                    ? 'text-[#00ff88] font-semibold'
                    : speedMinutes > 15 && speedMinutes <= 30
                        ? 'text-[#ffd93d]'
                        : speedMinutes > 30 && speedMinutes <= 60
                            ? 'text-orange-400'
                            : 'text-gray-500'
                    }`}>
                    {speedMinutes >= 0
                        ? speedMinutes >= 60
                            ? `${Math.floor(speedMinutes / 60)}h${speedMinutes % 60 > 0 ? ` ${speedMinutes % 60}m` : ''}`
                            : `${speedMinutes}m`
                        : '-'}
                </span>
            </td>

            {/* Pullback */}
            <td className="px-2 sm:px-3 md:px-5 py-2 sm:py-3 md:py-4 text-center">
                <span className={`font-mono text-[10px] sm:text-xs md:text-sm font-medium ${pullbackPercent <= 0.3 ? 'text-[#00ff88]' :
                    pullbackPercent <= 1.0 ? 'text-[#ffd93d]' : 'text-[#ff4757]'
                    }`}>
                    {typeof pullbackPercent === 'number' ? pullbackPercent.toFixed(1) : '0.0'}%
                </span>
            </td>

            {/* Decel */}
            <td className="px-2 sm:px-3 md:px-5 py-2 sm:py-3 md:py-4 text-center">
                <span className={`font-mono text-[10px] sm:text-xs md:text-sm font-medium ${decelPercent > 0 ? 'text-[#00ff88]' : decelPercent < 0 ? 'text-[#ff4757]' : 'text-gray-500'
                    }`}>
                    {typeof decelPercent === 'number' ? `${decelPercent.toFixed(1)}%` : '0.0%'}
                </span>
            </td>

            {/* Sparkline */}
            <td className="px-2 sm:px-3 md:px-5 py-2 sm:py-3 md:py-4">
                <div className="opacity-80 group-hover:opacity-100 transition-opacity">
                    <Sparkline
                        data={sparkline}
                        isPositive={isLong}
                        width={60}
                        height={24}
                        className="sm:w-[80px] sm:h-[30px] md:w-[100px] md:h-[36px]"
                    />
                </div>
            </td>

            {/* Score */}
            <td className="px-2 sm:px-3 md:px-5 py-2 sm:py-3 md:py-4 text-right">
                <ScoreBadge score={score} />
            </td>
        </tr>
    );
};

export default TableRow;
