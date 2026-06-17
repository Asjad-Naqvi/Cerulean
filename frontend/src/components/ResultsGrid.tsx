'use client';

import React from 'react';
import ProductCard from './ProductCard';
import { Product } from '../lib/types';

interface ResultsGridProps {
  products: Product[];
  isLoading: boolean;
}

export default function ResultsGrid({ products, isLoading }: ResultsGridProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="bg-slate-900/40 border border-white/5 rounded-2xl p-4 flex flex-col gap-3 animate-pulse">
            <div className="aspect-[3/4] bg-white/5 rounded-xl w-full" />
            <div className="h-4 bg-white/5 rounded w-1/3" />
            <div className="h-6 bg-white/5 rounded w-3/4" />
            <div className="h-5 bg-white/5 rounded w-1/2" />
            <div className="flex gap-1.5 mt-auto pt-2">
              <div className="h-5 bg-white/5 rounded w-6" />
              <div className="h-5 bg-white/5 rounded w-6" />
              <div className="h-5 bg-white/5 rounded w-6" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (products.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center p-12 border border-white/5 rounded-2xl bg-slate-900/20 backdrop-blur-sm">
        <svg className="w-16 h-16 text-slate-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
        </svg>
        <h3 className="text-lg font-semibold text-white mb-2">No outfits found</h3>
        <p className="text-slate-400 max-w-md">
          We couldn&apos;t find any matches. Try using different keywords, relaxing your price range, or clearing custom measurements.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6">
      {products.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}
