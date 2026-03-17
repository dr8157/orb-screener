import { useState, useEffect } from 'react';

/**
 * Custom hook for real-time clock
 * @param {number} updateInterval - Update interval in milliseconds (default: 1000)
 * @returns {Date} Current time as Date object
 */
export const useClock = (updateInterval = 1000) => {
    const [time, setTime] = useState(new Date());

    useEffect(() => {
        const timer = setInterval(() => {
            setTime(new Date());
        }, updateInterval);

        return () => clearInterval(timer);
    }, [updateInterval]);

    return time;
};

export default useClock;
