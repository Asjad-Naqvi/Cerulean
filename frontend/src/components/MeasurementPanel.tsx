'use client';

import React from 'react';

import { Measurements } from '../lib/types';

interface MeasurementPanelProps {
  measurements: Measurements;
  onChange: (measurements: Measurements) => void;
  isOpen: boolean;
  onClose: () => void;
}

export default function MeasurementPanel({ measurements, onChange, isOpen, onClose }: MeasurementPanelProps) {
  const handleInputChange = (field: keyof Measurements, val: string) => {
    const numVal = val === '' ? undefined : parseFloat(val);
    onChange({
      ...measurements,
      [field]: numVal
    });
  };

  const handleClear = () => {
    onChange({});
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div onClick={onClose} className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Drawer */}
      <div className="relative w-full max-w-md h-full bg-slate-900 border-l border-white/10 p-6 flex flex-col shadow-2xl transition-all duration-300">
        <div className="flex items-center justify-between border-b border-white/10 pb-4 mb-6">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <svg className="w-6 h-6 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
            </svg>
            <span>Custom Sizing (Inches)</span>
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors p-2">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <p className="text-sm text-slate-400 mb-6">
          Provide your measurements to filter search results by available sizes and map sizes to each store's custom chart.
        </p>

        <div className="space-y-6 flex-1">
          {/* Chest */}
          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold text-slate-300 flex justify-between">
              <span>Chest / Bust</span>
              {measurements.chest && <span className="text-teal-400 font-normal">{measurements.chest}&quot;</span>}
            </label>
            <input
              type="number"
              min="20"
              max="60"
              step="0.5"
              value={measurements.chest ?? ''}
              onChange={(e) => handleInputChange('chest', e.target.value)}
              placeholder="e.g. 36.5"
              className="bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white outline-none focus:border-teal-500 transition-colors placeholder-slate-600"
            />
          </div>

          {/* Waist */}
          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold text-slate-300 flex justify-between">
              <span>Waist</span>
              {measurements.waist && <span className="text-teal-400 font-normal">{measurements.waist}&quot;</span>}
            </label>
            <input
              type="number"
              min="20"
              max="60"
              step="0.5"
              value={measurements.waist ?? ''}
              onChange={(e) => handleInputChange('waist', e.target.value)}
              placeholder="e.g. 29.5"
              className="bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white outline-none focus:border-teal-500 transition-colors placeholder-slate-600"
            />
          </div>

          {/* Hips */}
          <div className="flex flex-col gap-2">
            <label className="text-sm font-semibold text-slate-300 flex justify-between">
              <span>Hips</span>
              {measurements.hips && <span className="text-teal-400 font-normal">{measurements.hips}&quot;</span>}
            </label>
            <input
              type="number"
              min="20"
              max="60"
              step="0.5"
              value={measurements.hips ?? ''}
              onChange={(e) => handleInputChange('hips', e.target.value)}
              placeholder="e.g. 39.5"
              className="bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white outline-none focus:border-teal-500 transition-colors placeholder-slate-600"
            />
          </div>
        </div>

        <div className="border-t border-white/10 pt-4 mt-6 flex gap-4">
          <button
            onClick={handleClear}
            className="flex-1 bg-white/5 hover:bg-white/10 border border-white/10 text-white font-medium py-3 rounded-xl transition-colors"
          >
            Clear All
          </button>
          <button
            onClick={onClose}
            className="flex-1 bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-600 hover:to-emerald-600 text-white font-medium py-3 rounded-xl transition-colors shadow-lg shadow-teal-500/25"
          >
            Apply Sizing
          </button>
        </div>
      </div>
    </div>
  );
}
