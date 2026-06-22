import { useContext } from 'react';
import { AnalysisContext } from '../context/analysisContextStore';

export const useAnalysis = () => {
  const context = useContext(AnalysisContext);

  if (!context) {
    throw new Error('useAnalysis must be used within an AnalysisProvider');
  }

  return context;
};
