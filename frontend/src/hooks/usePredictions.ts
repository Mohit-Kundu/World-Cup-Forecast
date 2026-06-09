import { useState, useEffect } from 'react';
import axios from 'axios';
import { PredictionsData } from '../types';
import { normalizePredictions } from '../utils/safeData';

const API_URL = import.meta.env.VITE_API_URL || '';

export function usePredictions() {
  const [data, setData] = useState<PredictionsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    const fetchPredictions = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await axios.get<PredictionsData>(
          `${API_URL}/api/predictions`,
          {
            signal: controller.signal,
            timeout: 120000,
          }
        );

        setData(normalizePredictions(response.data));
      } catch (err) {
        if (axios.isCancel(err)) return;

        console.error('Error fetching predictions:', err);

        if (axios.isAxiosError(err)) {
          if (err.code === 'ECONNABORTED') {
            setError('Request timed out. Backend still running sims — try again.');
          } else if (err.response) {
            setError(`Backend error (${err.response.status}). Check backend logs.`);
          } else {
            setError('Cannot reach backend. Run: python backend/api.py');
          }
        } else {
          setError('Failed to load predictions.');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchPredictions();
    return () => controller.abort();
  }, []);

  return { data, loading, error };
}
