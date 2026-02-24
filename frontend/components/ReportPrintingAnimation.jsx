'use client';

import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export default function ReportPrintingAnimation({ analysisComplete, onFinish }) {
  useEffect(() => {
    if (analysisComplete) {
      const timer = setTimeout(() => {
        if (onFinish) onFinish();
      }, 2500);
      return () => clearTimeout(timer);
    }
  }, [analysisComplete, onFinish]);

  return (
    <AnimatePresence>
      {analysisComplete && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center bg-[#f8fafc]"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.5 }}
        >
          <motion.div
            className="w-[480px] max-w-[90vw] h-[340px] bg-white rounded-2xl shadow-xl flex flex-col items-center justify-center p-10"
            initial={{ y: 500, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -100, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 60, damping: 18, duration: 0.7 }}
          >
            <h1 className="text-4xl font-serif font-bold text-gray-900 mb-4">Printing Report...</h1>
            <p className="text-lg text-gray-600 text-center">Your analysis is ready. Generating your full debate intelligence report.</p>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
