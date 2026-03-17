import React, { useState, useEffect } from 'react';
import { X, Save, RotateCcw, Settings, Sliders, Scale, Gauge, Loader2, Check } from 'lucide-react';
import ConfigSlider from './ConfigSlider';

/**
 * Premium Admin Configuration Modal
 */
const AdminModal = ({ config, onClose, onSave, onReset, isLoading }) => {
    const [localConfig, setLocalConfig] = useState({});
    const [hasChanges, setHasChanges] = useState(false);
    const [saveError, setSaveError] = useState(null);
    const [saveSuccess, setSaveSuccess] = useState(false);

    useEffect(() => {
        if (config) {
            // Ensure watchlist is preserved (required field)
            setLocalConfig({
                ...config,
                watchlist: config.watchlist || []
            });
        }
    }, [config]);

    const handleChange = (key, value) => {
        setLocalConfig(prev => ({ ...prev, [key]: value }));
        setHasChanges(true);
        setSaveError(null);
        setSaveSuccess(false);
    };

    const handleSave = async () => {
        if (!onSave) return;

        try {
            setSaveError(null);
            setSaveSuccess(false);

            // Auto-normalize weights to sum to 1.0
            const totalWeight = (
                (localConfig.weight_volume || 0) +
                (localConfig.weight_value || 0) +
                (localConfig.weight_body || 0) +
                (localConfig.weight_speed || 0) +
                (localConfig.weight_pullback || 0) +
                (localConfig.weight_decel || 0)
            );

            let normalizedConfig = { ...localConfig };
            if (totalWeight > 0 && Math.abs(totalWeight - 1.0) > 0.01) {
                // Normalize weights to sum to 1.0
                normalizedConfig = {
                    ...localConfig,
                    weight_volume: (localConfig.weight_volume || 0) / totalWeight,
                    weight_value: (localConfig.weight_value || 0) / totalWeight,
                    weight_body: (localConfig.weight_body || 0) / totalWeight,
                    weight_speed: (localConfig.weight_speed || 0) / totalWeight,
                    weight_pullback: (localConfig.weight_pullback || 0) / totalWeight,
                    weight_decel: (localConfig.weight_decel || 0) / totalWeight,
                };
                console.log('Weights normalized:', totalWeight, '-> 1.0');
            }

            // Ensure watchlist is included in the payload
            const configToSave = {
                ...normalizedConfig,
                watchlist: normalizedConfig.watchlist || []
            };

            console.log('Saving config:', configToSave);
            const result = await onSave(configToSave);
            console.log('Save result:', result);

            if (result) {
                setLocalConfig(normalizedConfig); // Update local with normalized values
                setHasChanges(false);
                setSaveSuccess(true);
                // Auto-close after successful save (with delay for visual feedback)
                setTimeout(() => {
                    onClose();
                }, 1000);
            } else {
                setSaveError('Failed to save configuration');
            }
        } catch (err) {
            console.error('Save error:', err);
            setSaveError('Failed to save configuration: ' + err.message);
        }
    };

    const handleReset = async () => {
        setSaveError(null);
        setSaveSuccess(false);
        await onReset?.();
        setHasChanges(false);
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div
                className="modal-content"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="modal-header">
                    <div className="flex items-center gap-2 sm:gap-3">
                        <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg sm:rounded-xl bg-gradient-to-br from-[#a855f7]/20 to-[#8b5cf6]/10 flex items-center justify-center border border-[#a855f7]/20">
                            <Settings className="w-4 h-4 sm:w-5 sm:h-5 text-[#a855f7]" />
                        </div>
                        <div>
                            <h2 className="modal-title text-base sm:text-lg">Configuration</h2>
                            <p className="text-[10px] sm:text-xs text-gray-500 mt-0.5">Adjust screener parameters</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="w-8 h-8 sm:w-9 sm:h-9 rounded-lg bg-black/30 border border-gray-800/50 flex items-center justify-center text-gray-400 hover:text-white hover:border-gray-600 transition-all"
                    >
                        <X className="w-4 h-4 sm:w-5 sm:h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-4 sm:p-6 space-y-6 sm:space-y-8">
                    {/* Baseline Settings */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 text-sm font-semibold text-[#00ff88]">
                            <Gauge className="w-4 h-4" />
                            <span>Baseline Settings</span>
                        </div>
                        <div className="grid gap-4 pl-6">
                            <ConfigSlider
                                label="Baseline Days"
                                value={localConfig.baseline_days || 20}
                                min={5}
                                max={60}
                                step={5}
                                onChange={(v) => handleChange('baseline_days', v)}
                            />
                        </div>
                    </div>

                    {/* Threshold Settings */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 text-sm font-semibold text-[#ffd93d]">
                            <Sliders className="w-4 h-4" />
                            <span>Threshold Settings</span>
                        </div>
                        <div className="grid gap-4 pl-6">
                            <ConfigSlider
                                label="Volume Multiplier"
                                value={localConfig.volume_multiplier || 5}
                                min={1}
                                max={20}
                                step={0.5}
                                suffix="x"
                                onChange={(v) => handleChange('volume_multiplier', v)}
                            />
                            <ConfigSlider
                                label="Value Threshold"
                                value={localConfig.value_threshold || 4}
                                min={1}
                                max={20}
                                step={0.5}
                                suffix=" Cr"
                                onChange={(v) => handleChange('value_threshold', v)}
                            />
                            <ConfigSlider
                                label="Body Threshold"
                                value={localConfig.body_threshold || 1.5}
                                min={0.5}
                                max={5}
                                step={0.1}
                                suffix="x"
                                onChange={(v) => handleChange('body_threshold', v)}
                            />
                            <ConfigSlider
                                label="Score Threshold"
                                value={localConfig.score_threshold || 0}
                                min={0}
                                max={100}
                                step={5}
                                onChange={(v) => handleChange('score_threshold', v)}
                            />
                            <ConfigSlider
                                label="Top N Display"
                                value={localConfig.top_n_display || 10}
                                min={5}
                                max={50}
                                step={5}
                                onChange={(v) => handleChange('top_n_display', v)}
                            />
                        </div>
                    </div>

                    {/* Weight Settings */}
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2 text-sm font-semibold text-[#5c7cfa]">
                                <Scale className="w-4 h-4" />
                                <span>Score Weights</span>
                            </div>
                            {/* Total Weight Display */}
                            {(() => {
                                const total = (
                                    (localConfig.weight_volume || 0) +
                                    (localConfig.weight_value || 0) +
                                    (localConfig.weight_body || 0) +
                                    (localConfig.weight_speed || 0) +
                                    (localConfig.weight_pullback || 0) +
                                    (localConfig.weight_decel || 0)
                                ) * 100;
                                const isValid = Math.abs(total - 100) < 1;
                                return (
                                    <span className={`text-xs font-mono px-2 py-1 rounded ${isValid
                                        ? 'bg-[#00ff88]/10 text-[#00ff88]'
                                        : 'bg-[#ff4757]/10 text-[#ff4757]'
                                        }`}>
                                        Total: {total.toFixed(0)}%
                                    </span>
                                );
                            })()}
                        </div>
                        <div className="grid gap-4 pl-6">
                            <ConfigSlider
                                label="Volume Weight"
                                value={(localConfig.weight_volume || 0.25) * 100}
                                min={0}
                                max={100}
                                step={5}
                                suffix="%"
                                onChange={(v) => handleChange('weight_volume', v / 100)}
                            />
                            <ConfigSlider
                                label="Value Weight"
                                value={(localConfig.weight_value || 0.25) * 100}
                                min={0}
                                max={100}
                                step={5}
                                suffix="%"
                                onChange={(v) => handleChange('weight_value', v / 100)}
                            />
                            <ConfigSlider
                                label="Body Weight"
                                value={(localConfig.weight_body || 0.2) * 100}
                                min={0}
                                max={100}
                                step={5}
                                suffix="%"
                                onChange={(v) => handleChange('weight_body', v / 100)}
                            />
                            <ConfigSlider
                                label="Speed Weight"
                                value={(localConfig.weight_speed || 0.15) * 100}
                                min={0}
                                max={100}
                                step={5}
                                suffix="%"
                                onChange={(v) => handleChange('weight_speed', v / 100)}
                            />
                            <ConfigSlider
                                label="Pullback Weight"
                                value={(localConfig.weight_pullback || 0.1) * 100}
                                min={0}
                                max={100}
                                step={5}
                                suffix="%"
                                onChange={(v) => handleChange('weight_pullback', v / 100)}
                            />
                            <ConfigSlider
                                label="Decel Weight"
                                value={(localConfig.weight_decel || 0.05) * 100}
                                min={0}
                                max={100}
                                step={5}
                                suffix="%"
                                onChange={(v) => handleChange('weight_decel', v / 100)}
                            />
                        </div>
                    </div>

                    {/* Scoring Formula Constants */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 text-sm font-semibold text-[#ff9f43]">
                            <Gauge className="w-4 h-4" />
                            <span>Scoring Formula</span>
                        </div>
                        <div className="grid gap-4 pl-6">
                            <ConfigSlider
                                label="Heat Max %"
                                value={localConfig.heat_max || 1000}
                                min={100}
                                max={5000}
                                step={100}
                                suffix="%"
                                onChange={(v) => handleChange('heat_max', v)}
                            />
                            <ConfigSlider
                                label="Speed Decay K"
                                value={localConfig.speed_decay_k || 30}
                                min={10}
                                max={120}
                                step={5}
                                suffix=" min"
                                onChange={(v) => handleChange('speed_decay_k', v)}
                            />
                            <ConfigSlider
                                label="PB Max %"
                                value={localConfig.pb_max || 5}
                                min={1}
                                max={20}
                                step={0.5}
                                suffix="%"
                                onChange={(v) => handleChange('pb_max', v)}
                            />
                        </div>
                    </div>
                </div>

                {/* Footer */}
                {saveError && (
                    <div className="px-4 sm:px-6 py-2 bg-[#ff4757]/10 border-t border-[#ff4757]/30">
                        <p className="text-[#ff4757] text-sm text-center">{saveError}</p>
                    </div>
                )}
                {saveSuccess && (
                    <div className="px-4 sm:px-6 py-2 bg-[#00ff88]/10 border-t border-[#00ff88]/30">
                        <p className="text-[#00ff88] text-sm text-center">✓ Configuration saved successfully!</p>
                    </div>
                )}
                <div className="px-4 sm:px-6 py-3 sm:py-4 border-t border-gray-800/50 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 sm:gap-0">
                    <button
                        onClick={handleReset}
                        disabled={isLoading}
                        className="flex items-center justify-center sm:justify-start gap-2 px-4 py-2.5 rounded-lg sm:rounded-xl text-gray-400 hover:text-white transition-colors order-3 sm:order-1"
                    >
                        <RotateCcw className="w-4 h-4" />
                        <span className="text-sm sm:text-base">Reset Defaults</span>
                    </button>
                    <div className="flex items-center gap-2 sm:gap-3 order-1 sm:order-2">
                        <button
                            onClick={onClose}
                            className="flex-1 sm:flex-none px-4 sm:px-5 py-2.5 rounded-lg sm:rounded-xl bg-black/30 border border-gray-800/50 text-gray-300 hover:bg-black/50 transition-all text-sm sm:text-base"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleSave}
                            disabled={isLoading || (!hasChanges && !saveSuccess)}
                            className={`flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 sm:px-5 py-2.5 rounded-lg sm:rounded-xl font-semibold disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg transition-all text-sm sm:text-base ${saveSuccess
                                ? 'bg-gradient-to-r from-[#00ff88] to-[#00cc6a] text-black hover:shadow-[#00ff88]/20'
                                : hasChanges
                                    ? 'bg-gradient-to-r from-[#00ff88] to-[#00cc6a] text-black hover:shadow-[#00ff88]/20'
                                    : 'bg-gray-700 text-gray-400'
                                }`}
                        >
                            {isLoading ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : saveSuccess ? (
                                <Check className="w-4 h-4" />
                            ) : (
                                <Save className="w-4 h-4" />
                            )}
                            <span>{saveSuccess ? 'Saved!' : 'Save Changes'}</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AdminModal;
