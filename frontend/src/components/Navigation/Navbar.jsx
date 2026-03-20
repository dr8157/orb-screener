import React, { useState } from 'react';
import { Clock, Settings, LogOut, Menu, X } from 'lucide-react';
import LiveIndicator from './LiveIndicator';

/**
 * Premium Navigation Bar - Mobile Responsive
 */
const Navbar = ({
    isConnected,
    isConnecting,
    error,
    currentTime,

    onAdminClick,
    onLogout,
    onReconnect,
}) => {
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    const handleAdminClick = () => {
        const password = prompt('Enter admin password:');
        if (password === 'orb@deepak2026') {
            onAdminClick?.();
        } else if (password !== null) {
            alert('Wrong password. Access denied.');
        }
    };


    const formatTime = (date) => {
        if (!date) return '--:--:--';
        return date.toLocaleTimeString('en-IN', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false,
        });
    };

    const toggleMobileMenu = () => {
        setIsMobileMenuOpen(!isMobileMenuOpen);
    };

    return (
        <nav className="navbar sticky top-0 z-50 px-4 sm:px-6 py-3 sm:py-4">
            <div className="max-w-[1800px] mx-auto">
                {/* Main Navbar Row */}
                <div className="flex items-center justify-between">
                    {/* Left: Logo & Live Status */}
                    <div className="flex items-center gap-3 sm:gap-6">
                        {/* Premium Logo */}
                        <div className="flex items-center gap-2 sm:gap-4">
                            {/* Logo Icon */}
                            <div className="relative group">
                                <div className="absolute inset-0 bg-gradient-to-r from-[#00ff88] to-[#00d4ff] rounded-lg sm:rounded-xl blur-lg opacity-40 group-hover:opacity-60 transition-opacity" />
                                <div className="relative w-9 h-9 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl bg-gradient-to-br from-[#00ff88] via-[#00cc6a] to-[#00aa55] flex items-center justify-center shadow-xl">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" className="text-black sm:w-6 sm:h-6">
                                        <path d="M3 17L9 11L13 15L21 7" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                                        <path d="M17 7H21V11" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                                    </svg>
                                </div>
                                {/* Pulse dot */}
                                <div className="absolute -top-0.5 -right-0.5 w-2 h-2 sm:w-3 sm:h-3">
                                    <div className="absolute inset-0 bg-[#00ff88] rounded-full animate-ping opacity-75" />
                                    <div className="relative w-2 h-2 sm:w-3 sm:h-3 bg-[#00ff88] rounded-full border-2 border-[#0a0e17]" />
                                </div>
                            </div>

                            {/* Brand Text - Hidden on very small screens */}
                            <div className="hidden xs:flex flex-col">
                                <div className="flex items-baseline gap-1">
                                    <span className="text-lg sm:text-2xl font-bold tracking-tight text-white">ORB</span>
                                    <span className="text-lg sm:text-2xl font-light tracking-tight bg-gradient-to-r from-[#00ff88] to-[#00d4ff] bg-clip-text text-transparent">Screener</span>
                                </div>
                                <span className="text-[8px] sm:text-[10px] font-medium tracking-[0.15em] sm:tracking-[0.2em] uppercase text-gray-500 hidden sm:block">Institutional Flow Scanner</span>
                            </div>
                        </div>

                        {/* Divider - Hidden on mobile */}
                        <div className="hidden lg:block h-10 w-px bg-gradient-to-b from-transparent via-gray-700 to-transparent" />

                        {/* Live Status */}
                        <LiveIndicator
                            isConnected={isConnected}
                            isConnecting={isConnecting}
                            error={error}
                            onReconnect={onReconnect}
                        />
                    </div>

                    {/* Center: Clock - Hidden on mobile, shown on tablet+ */}
                    <div className="hidden md:flex items-center gap-4">
                        <div className="flex items-center gap-2 sm:gap-3 px-3 sm:px-5 py-2 sm:py-2.5 rounded-lg sm:rounded-xl bg-black/40 border border-gray-800/50 backdrop-blur">
                            <Clock className="w-3 h-3 sm:w-4 sm:h-4 text-[#00ff88]" />
                            <div className="flex flex-col">
                                <span className="text-[8px] sm:text-[9px] text-gray-500 uppercase tracking-wider leading-none">IST</span>
                                <span className="clock-display text-sm sm:text-lg leading-tight">{formatTime(currentTime)}</span>
                            </div>
                        </div>
                    </div>

                    {/* Right: Desktop Controls - Hidden on mobile */}
                    <div className="hidden lg:flex items-center gap-2 sm:gap-3">

                        {/* Admin Button */}
                        <button
                            onClick={handleAdminClick}
                            className="flex items-center gap-2 px-3 sm:px-4 py-2 sm:py-2.5 rounded-lg sm:rounded-xl bg-black/40 border border-gray-800/50 text-gray-400 hover:text-[#a855f7] hover:border-[#a855f7]/30 transition-all backdrop-blur"
                            title="Admin Settings"
                        >
                            <Settings className="w-4 h-4" />
                            <span className="text-sm hidden xl:inline">Admin</span>
                        </button>

                        {/* Logout */}
                        <button
                            onClick={onLogout}
                            className="flex items-center gap-2 px-3 sm:px-4 py-2 sm:py-2.5 rounded-lg sm:rounded-xl bg-[#ff4757]/10 border border-[#ff4757]/30 text-[#ff4757] hover:bg-[#ff4757]/20 transition-all"
                            title="Logout"
                        >
                            <LogOut className="w-4 h-4" />
                        </button>
                    </div>

                    {/* Mobile Menu Button - Shown only on mobile/tablet */}
                    <button
                        onClick={toggleMobileMenu}
                        className="lg:hidden flex items-center justify-center w-10 h-10 rounded-lg bg-black/40 border border-gray-800/50 text-gray-400 hover:text-white transition-all"
                        aria-label="Toggle menu"
                    >
                        {isMobileMenuOpen ? (
                            <X className="w-5 h-5" />
                        ) : (
                            <Menu className="w-5 h-5" />
                        )}
                    </button>
                </div>

                {/* Mobile Menu Dropdown */}
                <div
                    className={`lg:hidden overflow-hidden transition-all duration-300 ease-in-out ${isMobileMenuOpen ? 'max-h-96 opacity-100 mt-4' : 'max-h-0 opacity-0'
                        }`}
                >
                    <div className="flex flex-col gap-3 pt-4 border-t border-gray-800/50">
                        {/* Mobile Clock */}
                        <div className="md:hidden flex items-center justify-between px-3 py-2 rounded-lg bg-black/30">
                            <div className="flex items-center gap-2">
                                <Clock className="w-4 h-4 text-[#00ff88]" />
                                <span className="text-xs text-gray-500 uppercase">IST</span>
                            </div>
                            <span className="clock-display text-base font-semibold">{formatTime(currentTime)}</span>
                        </div>

                        {/* Action Buttons - Mobile */}
                        <div className="grid grid-cols-2 gap-2">
                            <button
                                onClick={() => {
                                    handleAdminClick();
                                    setIsMobileMenuOpen(false);
                                }}
                                className="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-black/40 border border-gray-800/50 text-gray-400 hover:text-[#a855f7] hover:border-[#a855f7]/30 transition-all"
                            >
                                <Settings className="w-4 h-4" />
                                <span className="text-sm">Admin</span>
                            </button>
                        </div>

                        {/* Logout - Mobile */}
                        <button
                            onClick={() => {
                                onLogout?.();
                                setIsMobileMenuOpen(false);
                            }}
                            className="flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-[#ff4757]/10 border border-[#ff4757]/30 text-[#ff4757] hover:bg-[#ff4757]/20 transition-all"
                        >
                            <LogOut className="w-4 h-4" />
                            <span className="text-sm">Logout</span>
                        </button>
                    </div>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
