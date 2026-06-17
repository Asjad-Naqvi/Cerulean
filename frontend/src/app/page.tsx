'use client';

import React, { useState } from 'react';
import SearchBar from '../components/SearchBar';
import VisualUpload from '../components/VisualUpload';
import MeasurementPanel from '../components/MeasurementPanel';
import ResultsGrid from '../components/ResultsGrid';
import StoreStatusBar from '../components/StoreStatusBar';
import AgentStatusBadge from '../components/AgentStatusBadge';
import { searchByText, searchByImage } from '../lib/api';
import { Product, SearchResponse, Measurements } from '../lib/types';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'text' | 'image'>('text');
  const [measurements, setMeasurements] = useState<Measurements>({});
  const [gender, setGender] = useState<'any' | 'men' | 'women' | 'kids'>('any');
  const [isSizingOpen, setIsSizingOpen] = useState(false);
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<SearchResponse | null>(null);

  const handleTextSearch = async (query: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await searchByText(
        query,
        hasMeasurements ? (measurements as Record<string, number>) : undefined,
        gender
      );
      setResponse(res);
    } catch (err: any) {
      setError(err.message || 'An error occurred during search.');
      setResponse(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleImageUpload = async (file: File) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await searchByImage(
        file,
        hasMeasurements ? (measurements as Record<string, number>) : undefined,
        gender
      );
      setResponse(res);
    } catch (err: any) {
      setError(err.message || 'An error occurred during image search.');
      setResponse(null);
    } finally {
      setIsLoading(false);
    }
  };

  const activeMeasurementsCount = Object.values(measurements).filter(v => v !== undefined).length;
  const hasMeasurements = activeMeasurementsCount > 0;

  return (
    <main className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col items-center">
      {/* Background gradients */}
      <div className="absolute inset-0 bg-gradient-to-tr from-[#0d1527] via-[#090d16] to-[#0c1a24] -z-10" />
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-teal-500/10 rounded-full blur-[120px] -z-10 pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-emerald-500/5 rounded-full blur-[120px] -z-10 pointer-events-none" />

      <div className="w-full max-w-6xl px-4 py-8 sm:py-12 flex flex-col gap-8">
        
        {/* Header */}
        <header className="flex flex-col md:flex-row items-center justify-between gap-6 border-b border-white/5 pb-6">
          <div className="text-center md:text-left">
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight bg-gradient-to-r from-teal-400 via-emerald-400 to-teal-500 bg-clip-text text-transparent">
              Cerulean
            </h1>
            <p className="text-slate-400 text-sm sm:text-base mt-1.5 font-medium">
              Live multi-agent Pakistani fashion finder
            </p>
          </div>
          
          <button
            onClick={() => setIsSizingOpen(true)}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl border text-sm font-semibold transition-all duration-300 shadow-md ${
              hasMeasurements
                ? 'bg-teal-500/15 border-teal-500/30 text-teal-400 hover:bg-teal-500/20'
                : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10'
            }`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
            </svg>
            <span>{hasMeasurements ? 'Sizing Customised' : 'Add Sizing Limits'}</span>
            {hasMeasurements && (
              <span className="bg-teal-500 text-slate-900 text-xs px-1.5 py-0.5 rounded-full font-extrabold">
                {activeMeasurementsCount}
              </span>
            )}
          </button>
        </header>

        {/* Tab Controls & Searching */}
        <section className="flex flex-col gap-6 items-center">
          <div className="bg-white/5 p-1 rounded-xl border border-white/10 flex">
            <button
              onClick={() => {
                setActiveTab('text');
                setError(null);
              }}
              className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all ${
                activeTab === 'text'
                  ? 'bg-slate-800 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Text Search
            </button>
            <button
              onClick={() => {
                setActiveTab('image');
                setError(null);
              }}
              className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all ${
                activeTab === 'image'
                  ? 'bg-slate-800 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Image Match
            </button>
          </div>

          <div className="w-full max-w-3xl flex flex-col gap-4">
            {activeTab === 'text' ? (
              <SearchBar onSearch={handleTextSearch} isLoading={isLoading} />
            ) : (
              <VisualUpload onUpload={handleImageUpload} isLoading={isLoading} />
            )}

            {/* Gender Selector Section */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mt-2">
              <span className="text-xs font-extrabold uppercase tracking-widest text-slate-400">
                Target Section:
              </span>
              <div className="bg-white/5 p-1 rounded-xl border border-white/10 flex gap-1 shadow-inner">
                {(['any', 'men', 'women', 'kids'] as const).map((g) => (
                  <button
                    key={g}
                    onClick={() => setGender(g)}
                    className={`px-4 py-1.5 rounded-lg text-xs font-bold capitalize transition-all duration-300 ${
                      gender === g
                        ? 'bg-gradient-to-r from-teal-500 to-emerald-500 text-slate-900 shadow-md font-extrabold scale-105'
                        : 'text-slate-300 hover:text-white hover:bg-white/5'
                    }`}
                  >
                    {g}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Status Indicators & Search Summary */}
        {response && (
          <section className={`grid grid-cols-1 ${response.style_concept_image ? 'md:grid-cols-3' : ''} gap-6 w-full`}>
            <div className={`${response.style_concept_image ? 'md:col-span-2' : ''} flex flex-col gap-4`}>
              <h2 className="text-lg font-semibold text-slate-200 bg-white/5 border border-white/5 rounded-2xl px-5 py-3 shadow-sm border-l-4 border-l-teal-500 leading-snug">
                {response.search_summary}
              </h2>
              <StoreStatusBar
                storesQueried={response.stores_queried}
                storesResponded={response.stores_responded}
                failedStores={response.failed_stores}
              />
              <AgentStatusBadge retrievalIterations={response.retrieval_iterations} />
            </div>
            {response.style_concept_image && (
              <div className="bg-white/5 border border-white/10 rounded-2xl p-4 flex flex-col items-center justify-center gap-3 shadow-lg relative overflow-hidden group">
                <div className="absolute inset-0 bg-gradient-to-br from-teal-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
                <div className="relative w-full aspect-square max-h-[200px] rounded-xl overflow-hidden border border-white/10 shadow-inner">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={response.style_concept_image}
                    alt="AI Style Concept"
                    className="w-full h-full object-cover transform hover:scale-105 transition-transform duration-500"
                  />
                </div>
                <div className="text-center z-10">
                  <span className="text-xs font-bold tracking-wider uppercase text-teal-400 bg-teal-500/10 px-2.5 py-1 rounded-full border border-teal-500/20">
                    Style Concept
                  </span>
                  <p className="text-xs text-slate-400 mt-2 italic">
                    AI generated style inspiration for your query
                  </p>
                </div>
              </div>
            )}
          </section>
        )}

        {/* Error State Banner */}
        {error && (
          <section className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-5 rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-4 shadow-lg">
            <div className="flex items-center gap-3">
              <svg className="w-6 h-6 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div>
                <p className="font-bold">Search Failed</p>
                <p className="text-sm text-slate-300 mt-0.5">{error}</p>
              </div>
            </div>
            <button
              onClick={() => {
                setError(null);
                if (activeTab === 'text') {
                  // Re-trigger text search
                }
              }}
              className="bg-rose-500 hover:bg-rose-600 text-white font-semibold text-sm px-4 py-2 rounded-xl transition-colors shrink-0"
            >
              Clear error
            </button>
          </section>
        )}

        {/* Results Grid */}
        <section className="mt-4">
          <h2 className="text-xl font-extrabold text-white mb-6 tracking-tight flex items-center gap-2">
            <span>Results</span>
            {response && (
              <span className="bg-teal-500/10 border border-teal-500/20 text-teal-400 text-xs px-2.5 py-1 rounded-full font-bold">
                {response.total_count} items found
              </span>
            )}
          </h2>
          <ResultsGrid products={response?.results || []} isLoading={isLoading} />
        </section>
      </div>

      {/* Sizing Panel Modal */}
      <MeasurementPanel
        measurements={measurements}
        onChange={setMeasurements}
        isOpen={isSizingOpen}
        onClose={() => setIsSizingOpen(false)}
      />
    </main>
  );
}
