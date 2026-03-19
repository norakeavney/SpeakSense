'use client';

import React, { useMemo } from 'react';

export default function WordCloud({ words = [], height = 300, maxWords = 50 }) {
  if (!words || words.length === 0) {
    return (
      <div className="flex items-center justify-center" style={{ height }}>
        <p className="text-gray-400 text-sm">No words to display</p>
      </div>
    );
  }

  // Calculate word sizes and positions
  const displayWords = words.slice(0, maxWords);
  
  // Normalize scores to get font sizes (14px to 42px range)
  const wordData = useMemo(() => {
    const minScore = Math.min(...displayWords.map(w => w.score || 0.5));
    const maxScore = Math.max(...displayWords.map(w => w.score || 0.5));
    const scoreRange = maxScore - minScore || 1;
    
    return displayWords.map((word, index) => {
      const score = word.score || 0.5;
      const normalizedScore = (score - minScore) / scoreRange;
      const fontSize = 14 + normalizedScore * 28; // 14px to 42px
      
      // Color based on score (gradient from pastel blue to pastel purple)
      const hue = 200 + normalizedScore * 60; // 200 (blue) to 260 (purple)
      const saturation = 40 + normalizedScore * 30; // 40% to 70%
      const lightness = 60 - normalizedScore * 10; // 60% to 50%
      const color = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
      
      return {
        word: word.word || word,
        fontSize,
        color,
        score: (score * 100).toFixed(1),
        index
      };
    });
  }, [displayWords]);

  // Calculate positions using a simple random layout
  const positions = useMemo(() => {
    const positioned = [];
    const width = 100; // percentage
    const containerHeight = 100; // percentage
    
    wordData.forEach((item, index) => {
      // Use a seed-based pseudo-random for consistent positioning
      const seed = index * 12.9898;
      const rand1 = Math.sin(seed) * 43758.5453 % 1;
      const rand2 = Math.sin(seed * 78.233) * 43758.5453 % 1;
      
      const left = rand1 * 85; // Leave margin
      const top = rand2 * 85;
      
      positioned.push({
        ...item,
        left,
        top,
      });
    });
    
    return positioned;
  }, [wordData]);

  return (
    <div 
      className="relative w-full border border-gray-200 rounded-lg bg-white overflow-hidden"
      style={{ height }}
    >
      <div className="absolute inset-0 flex flex-wrap content-start gap-1 p-4 overflow-hidden">
        {positions.map((item, index) => (
          <div
            key={`${item.word}-${index}`}
            className="absolute whitespace-nowrap font-semibold transition-all duration-300 hover:scale-110 cursor-default select-none"
            style={{
              fontSize: `${item.fontSize}px`,
              color: item.color,
              left: `${item.left}%`,
              top: `${item.top}%`,
              opacity: 0.85,
              textShadow: '0 1px 3px rgba(0,0,0,0.1)',
            }}
            title={`${item.word}: ${item.score}%`}
          >
            {item.word}
          </div>
        ))}
      </div>
    </div>
  );
}
