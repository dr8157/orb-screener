import React, { useState, useMemo } from 'react';
import { BarChart3, WifiOff, Zap, Activity, ChevronUp, ChevronDown, ArrowUpDown } from 'lucide-react';
import TableRow from './TableRow';

/**
 * Premium Rankings Table with glassmorphism, animations, and sorting
 */
const RankingsTable = ({ signals = [], isConnected, lastUpdate }) => {
    const [sortKey, setSortKey] = useState('score');
    const [sortDirection, setSortDirection] = useState('desc');

    const formatLastUpdate = (date) => {
        if (!date) return 'Never';
        return date.toLocaleTimeString('en-IN', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
        });
    };

    // Column definitions with sortable flag and actual data key
    const columns = [
        { key: 'rank', dataKey: 'rank', label: '#', align: 'left', sortable: false },
        { key: 'symbol', dataKey: 'symbol', label: 'Symbol', align: 'left', sortable: true },
        { key: 'time', dataKey: 'time', label: 'Time', align: 'left', sortable: false },
        { key: 'dir', dataKey: 'dir', label: 'Dir', align: 'left', sortable: false },
        { key: 'price', dataKey: 'price', label: 'Price', align: 'right', sortable: true },
        { key: 'change', dataKey: 'changePercent', label: 'Chg %', align: 'right', sortable: true },
        { key: 'volume', dataKey: 'volumeRaw', label: 'Volume', align: 'left', sortable: true },
        { key: 'dayVolume', dataKey: 'dayVolumeRaw', label: 'Day Vol', align: 'left', sortable: true },
        { key: 'value', dataKey: 'value', label: 'Value', align: 'left', sortable: true },
        { key: 'body', dataKey: 'body', label: 'Body', align: 'left', sortable: true },
        { key: 'orb', dataKey: 'orbValid', label: 'ORB', align: 'center', sortable: false },
        { key: 'speed', dataKey: 'speedMinutes', label: 'Speed', align: 'center', sortable: true },
        { key: 'pb', dataKey: 'pullbackPercent', label: 'PB', align: 'center', sortable: true },
        { key: 'decel', dataKey: 'decelPercent', label: 'Decel', align: 'center', sortable: true },
        { key: 'chart', dataKey: null, label: 'Chart', align: 'center', sortable: false },
        { key: 'score', dataKey: 'score', label: 'Score', align: 'right', sortable: true },
    ];

    // Handle column header click for sorting
    const handleSort = (col) => {
        if (!col.sortable || !col.dataKey) return;

        if (sortKey === col.dataKey) {
            setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
        } else {
            setSortKey(col.dataKey);
            setSortDirection('desc');
        }
    };

    // Sort signals based on current sort settings
    const sortedSignals = useMemo(() => {
        if (!signals.length) return [];

        return [...signals].sort((a, b) => {
            let aVal = a[sortKey];
            let bVal = b[sortKey];

            // Handle string comparison for symbol
            if (sortKey === 'symbol') {
                aVal = aVal || '';
                bVal = bVal || '';
                return sortDirection === 'asc'
                    ? aVal.localeCompare(bVal)
                    : bVal.localeCompare(aVal);
            }

            // Handle numeric comparison
            aVal = typeof aVal === 'number' ? aVal : 0;
            bVal = typeof bVal === 'number' ? bVal : 0;

            return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
        });
    }, [signals, sortKey, sortDirection]);

    // Get sort icon for column
    const getSortIcon = (col) => {
        if (!col.sortable) return null;

        if (sortKey === col.dataKey) {
            return sortDirection === 'asc'
                ? <ChevronUp className="w-3 h-3 text-[#00ff88]" />
                : <ChevronDown className="w-3 h-3 text-[#00ff88]" />;
        }

        return <ArrowUpDown className="w-3 h-3 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity" />;
    };

    return (
        <div className="glass-container overflow-hidden">
            {/* Header */}
            <div className="table-header">
                <div className="table-title">
                    <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg sm:rounded-xl bg-gradient-to-br from-[#00ff88]/20 to-[#00cc6a]/10 flex items-center justify-center border border-[#00ff88]/20">
                        <Zap className="w-4 h-4 sm:w-5 sm:h-5 text-[#00ff88]" />
                    </div>
                    <div>
                        <h2 className="text-base sm:text-lg font-semibold">Top Spike Rankings</h2>
                        <p className="text-[10px] sm:text-xs text-gray-500 mt-0.5">Real-time institutional flow analysis</p>
                    </div>
                </div>

                <div className="table-meta flex-wrap">
                    <div className="flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-1 sm:py-1.5 rounded-md sm:rounded-lg bg-black/20">
                        <Activity className="w-3 h-3 sm:w-4 sm:h-4 text-[#00ff88]" />
                        <span className="font-semibold text-white text-sm sm:text-base">{signals.length}</span>
                        <span className="text-gray-500 text-xs sm:text-sm">signals</span>
                    </div>
                    <div className="flex items-center gap-1.5 sm:gap-2 text-gray-500 text-xs sm:text-sm">
                        <span>Updated:</span>
                        <span className="font-mono text-gray-400">{formatLastUpdate(lastUpdate)} IST</span>
                    </div>
                </div>
            </div>

            {/* Table Content */}
            {!isConnected ? (
                <div className="empty-state">
                    <div className="w-14 h-14 sm:w-20 sm:h-20 rounded-xl sm:rounded-2xl bg-[#ff4757]/10 flex items-center justify-center mb-4 sm:mb-6">
                        <WifiOff className="w-7 h-7 sm:w-10 sm:h-10 text-[#ff4757]" />
                    </div>
                    <h3 className="text-lg sm:text-xl font-semibold text-white mb-2">Not Connected</h3>
                    <p className="text-gray-400 max-w-xs sm:max-w-md text-sm sm:text-base text-center">
                        Waiting for connection to the backend server at localhost:8000
                    </p>
                </div>
            ) : signals.length === 0 ? (
                <div className="empty-state">
                    <div className="w-14 h-14 sm:w-20 sm:h-20 rounded-xl sm:rounded-2xl bg-[#ffd93d]/10 flex items-center justify-center mb-4 sm:mb-6">
                        <BarChart3 className="w-7 h-7 sm:w-10 sm:h-10 text-[#ffd93d]" />
                    </div>
                    <h3 className="text-lg sm:text-xl font-semibold text-white mb-2">Waiting for Signals</h3>
                    <p className="text-gray-400 max-w-xs sm:max-w-md text-sm sm:text-base text-center">
                        No breakout signals detected yet. Signals will appear when stocks break their ORB range.
                    </p>
                </div>
            ) : (
                <div className="overflow-x-auto">
                    <table className="data-table">
                        <thead>
                            <tr>
                                {columns.map((col) => (
                                    <th
                                        key={col.key}
                                        className={`text-${col.align} ${col.sortable ? 'cursor-pointer hover:bg-white/5 group' : ''} ${sortKey === col.dataKey ? 'text-[#00ff88]' : ''}`}
                                        onClick={() => handleSort(col)}
                                    >
                                        <div className="flex items-center gap-1 justify-center">
                                            <span>{col.label}</span>
                                            {getSortIcon(col)}
                                        </div>
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {sortedSignals.map((signal, idx) => (
                                <TableRow
                                    key={`${signal.symbol}-${idx}`}
                                    signal={{ ...signal, rank: idx + 1 }}
                                    isNew={signal.score >= 90}
                                />
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Legend */}
            {signals.length > 0 && (
                <div className="table-legend">
                    <div className="legend-item">
                        <div className="legend-dot excellent" />
                        <span>90+ Excellent</span>
                    </div>
                    <div className="legend-item">
                        <div className="legend-dot good" />
                        <span>80+ Good</span>
                    </div>
                    <div className="legend-item">
                        <div className="legend-dot average" />
                        <span>70+ Average</span>
                    </div>
                    <div className="legend-item">
                        <div className="legend-dot low" />
                        <span>&lt;70 Low</span>
                    </div>
                    <div className="flex-1" />
                    <div className="text-gray-600 text-xs">
                        Heat % = Current vs 20-day baseline | Click headers to sort
                    </div>
                </div>
            )}
        </div>
    );
};

export default RankingsTable;

