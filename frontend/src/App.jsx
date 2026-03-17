import React, { useState } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { useClock } from './hooks/useClock';
import { useConfig } from './hooks/useConfig';
import Navbar from './components/Navigation/Navbar';
import RankingsTable from './components/Table/RankingsTable';
import AdminModal from './components/Admin/AdminModal';
import './App.css';

/**
 * ORB Institutional Screener - Main Application
 */
function App() {
  const [showAdmin, setShowAdmin] = useState(false);

  // Hooks
  const {
    signals,
    isConnected,
    isConnecting,
    error,
    lastUpdate,
    reconnect
  } = useWebSocket(5000);

  const currentTime = useClock(1000);
  const { config, updateConfig, resetConfig, isLoading: configLoading } = useConfig();


  // Handle logout (placeholder)
  const handleLogout = () => {
    console.log('Logout clicked');
  };

  return (
    <div className="min-h-screen">
      {/* Navbar */}
      <Navbar
        isConnected={isConnected}
        isConnecting={isConnecting}
        error={error}
        currentTime={currentTime}
        onAdminClick={() => setShowAdmin(true)}
        onLogout={handleLogout}
        onReconnect={reconnect}
      />

      {/* Main Content */}
      <main className="max-w-[1800px] mx-auto px-3 sm:px-4 md:px-6 py-4 sm:py-6">
        <RankingsTable
          signals={signals}
          isConnected={isConnected}
          lastUpdate={lastUpdate}
        />
      </main>

      {/* Admin Modal */}
      {showAdmin && (
        <AdminModal
          config={config}
          onClose={() => setShowAdmin(false)}
          onSave={updateConfig}
          onReset={resetConfig}
          isLoading={configLoading}
        />
      )}
    </div>
  );
}

export default App;
