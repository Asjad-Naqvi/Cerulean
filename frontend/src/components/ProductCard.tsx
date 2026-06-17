'use client';

import React from 'react';
import { Product } from '../lib/types';

interface ProductCardProps {
  product: Product;
}

export default function ProductCard({ product }: ProductCardProps) {
  const isSale = product.compare_price && product.compare_price > product.price;

  return (
    <div className="group relative flex flex-col bg-slate-900/60 backdrop-blur-md rounded-2xl border border-white/10 overflow-hidden hover:border-teal-500/30 hover:shadow-2xl hover:shadow-teal-500/5 transition-all duration-300">
      {/* Aspect Ratio Container for Image */}
      <div className="relative aspect-[3/4] w-full bg-slate-950 overflow-hidden">
        {isSale && (
          <div className="absolute top-3 left-3 z-10 bg-rose-500 text-white text-xs font-bold px-2.5 py-1 rounded-full shadow-md">
            SALE
          </div>
        )}
        {product.relevance_score !== null && (
          <div className="absolute top-3 right-3 z-10 bg-teal-500/90 backdrop-blur-md text-white text-xs font-semibold px-2.5 py-1 rounded-full shadow-md border border-teal-400/20">
            {Math.round(product.relevance_score * 100)}% Match
          </div>
        )}
        {product.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={product.image_url}
            alt={product.title}
            className="w-full h-full object-cover object-top group-hover:scale-105 transition-transform duration-500"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center text-slate-500 gap-2">
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span className="text-xs">No image available</span>
          </div>
        )}
        
        {/* Hover overlay button */}
        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-4">
          <a
            href={product.product_url}
            target="_blank"
            rel="noopener noreferrer"
            className="w-full text-center bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-600 hover:to-emerald-600 text-white text-sm font-semibold py-2.5 rounded-xl shadow-lg transition-all transform translate-y-2 group-hover:translate-y-0 duration-300"
          >
            Shop Now →
          </a>
        </div>
      </div>

      {/* Details */}
      <div className="p-4 flex flex-col flex-1 gap-2.5">
        <div className="flex items-center justify-between gap-2">
          <span className="bg-white/5 border border-white/10 text-teal-400 text-xs font-semibold px-2 py-0.5 rounded-md uppercase tracking-wider">
            {product.store_name}
          </span>
        </div>

        <h3 className="font-semibold text-white text-sm sm:text-base leading-tight line-clamp-2 min-h-[2.5rem] group-hover:text-teal-400 transition-colors">
          {product.title}
        </h3>

        {/* Pricing */}
        <div className="flex items-baseline gap-2">
          <span className="text-base sm:text-lg font-bold text-white">
            Rs. {Math.round(product.price).toLocaleString()}
          </span>
          {isSale && product.compare_price && (
            <span className="text-xs sm:text-sm text-slate-500 line-through">
              Rs. {Math.round(product.compare_price).toLocaleString()}
            </span>
          )}
        </div>

        {/* Sizes */}
        <div className="flex flex-wrap gap-1.5 mt-auto pt-2">
          {product.available_sizes.slice(0, 5).map((size) => {
            const isMatched = product.matched_size === size;
            return (
              <span
                key={size}
                className={`text-[10px] sm:text-xs font-medium px-2 py-0.5 rounded-md border ${
                  isMatched
                    ? 'bg-teal-500 text-white border-teal-400 font-bold shadow-md shadow-teal-500/20'
                    : 'bg-white/5 text-slate-400 border-white/5'
                }`}
              >
                {size}
              </span>
            );
          })}
          {product.available_sizes.length > 5 && (
            <span className="text-[10px] sm:text-xs text-slate-500 px-1 py-0.5 self-center font-medium">
              +{product.available_sizes.length - 5} more
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
