'use client';

import React from 'react';

interface StoreStatusBarProps {
  storesQueried: number;
  storesResponded: number;
  failedStores: string[];
}

export default function StoreStatusBar({ storesQueried, storesResponded, failedStores }: StoreStatusBarProps) {
  if (storesQueried === 0) return null;

  const failedCount = failedStores.length;
  const successRate = storesQueried > 0 ? (storesResponded / storesQueried) * 100 : 0;

  return (
    <div className="w-full bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-2xl p-4 flex flex-col md:flex-row items-center justify-between gap-4 shadow-lg">
      <div className="flex items-center gap-3">
        <div className="relative flex h-3 w-3">
          <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${failedCount === storesQueried ? 'bg-rose-400' : 'bg-emerald-400'}`}></span>
          <span className={`relative inline-flex rounded-full h-3 w-3 ${failedCount === storesQueried ? 'bg-rose-500' : 'bg-emerald-500'}`}></span>
        </div>
        <p className="text-sm text-slate-300 font-medium">
          Checked <span className="text-white font-bold">{storesQueried}</span> store{storesQueried > 1 ? 's' : ''} ·{' '}
          <span className="text-emerald-400 font-bold">{storesResponded}</span> responded ·{' '}
          {failedCount > 0 ? (
            <span className="text-rose-400 font-bold">{failedCount} failed</span>
          ) : (
            <span className="text-emerald-400">0 failures</span>
          )}
        </p>
      </div>

      {/* Progress indicators or failure tags */}
      <div className="flex flex-wrap items-center gap-2">
        {failedCount > 0 && (
          <div className="flex items-center gap-1.5 text-xs bg-rose-500/10 border border-rose-500/20 text-rose-400 px-3 py-1.5 rounded-full">
            <span className="font-semibold">Failed stores:</span>
            <span>{failedStores.map(slug => slug.toUpperCase()).join(', ')}</span>
          </div>
        )}
        <div className="h-1.5 w-24 bg-white/10 rounded-full overflow-hidden hidden sm:block">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              successRate > 80 ? 'bg-emerald-500' : successRate > 50 ? 'bg-amber-500' : 'bg-rose-500'
            }`}
            style={{ width: `${successRate}%` }}
          />
        </div>
      </div>
    </div>
  );
}
