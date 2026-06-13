import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { PredictionsData } from '../types';
import { normalizePredictions } from '../utils/safeData';

const API_URL = import.meta.env.VITE_API_URL || '';

const MIN_ITERATIONS = 10;
const MAX_ITERATIONS = 5000;
const DEFAULT_ITERATIONS = 200;

interface SimulationControlProps {
  onDataLoaded: (data: PredictionsData) => void;
}

export const SimulationControl: React.FC<SimulationControlProps> = ({ onDataLoaded }) => {
  const [loading, setLoading] = useState(true);
  const [iterations, setIterations] = useState(DEFAULT_ITERATIONS);
  const [simulating, setSimulating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dataLoaded, setDataLoaded] = useState(false);

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      setLoading(true);
      const response = await axios.get<{ has_predictions: boolean }>(
        `${API_URL}/api/predictions/status`
      );

      if (response.data.has_predictions) {
        await loadPredictions();
      }
    } catch (err) {
      console.error('Error checking status:', err);
      setError('Failed to check predictions status');
    } finally {
      setLoading(false);
    }
  };

  const loadPredictions = async () => {
    try {
      setLoading(true);
      const response = await axios.get<PredictionsData>(
        `${API_URL}/api/predictions`,
        { timeout: 30000 }
      );
      const normalized = normalizePredictions(response.data);
      onDataLoaded(normalized);
      setDataLoaded(true);
      setError(null);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 404) {
        setDataLoaded(false);
      } else {
        setError('Failed to load predictions');
        console.error(err);
      }
    } finally {
      setLoading(false);
    }
  };

  const runSimulation = async () => {
    try {
      setSimulating(true);
      setError(null);

      const response = await axios.post<PredictionsData>(
        `${API_URL}/api/simulate`,
        { n_simulations: iterations },
        { timeout: 300000 }
      );

      const normalized = normalizePredictions(response.data);
      onDataLoaded(normalized);
      setDataLoaded(true);

      await checkStatus();
    } catch (err) {
      console.error('Simulation error:', err);
      if (axios.isAxiosError(err)) {
        if (err.response?.status === 400) {
          setError(`Invalid request: ${err.response.data.detail}`);
        } else if (err.code === 'ECONNABORTED') {
          setError('Simulation timed out. Try fewer iterations.');
        } else {
          setError('Simulation failed. Check backend logs.');
        }
      } else {
        setError('Simulation failed');
      }
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="flex w-full flex-col gap-2 sm:w-auto sm:items-end">
      <div className="flex flex-col gap-2 md:flex-row md:items-center">
        <label htmlFor="iterations" className="shrink-0 text-sm text-muted">
          Iterations:
        </label>
        <div className="flex items-center gap-2">
          <input
            id="iterations"
            type="number"
            min={MIN_ITERATIONS}
            max={MAX_ITERATIONS}
            value={iterations}
            onChange={(e) => setIterations(Number(e.target.value))}
            disabled={simulating}
            className="h-8 w-20 rounded-md border border-muted/50 bg-background px-2 py-1 text-sm text-primary focus:border-gold focus:outline-none disabled:opacity-50"
          />
          <button
            onClick={runSimulation}
            disabled={simulating || loading}
            className="inline-flex h-8 min-w-[8.75rem] shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-md bg-gold px-3 py-1 text-sm font-medium text-black transition-opacity hover:opacity-90 disabled:opacity-50 md:min-w-[9.75rem]"
          >
            {simulating && (
              <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-black/30 border-t-black" />
            )}
            {dataLoaded ? 'Re-run Simulation' : 'Run Simulation'}
          </button>
        </div>
      </div>

      {error && (
        <p className="text-xs text-red-400">{error}</p>
      )}
    </div>
  );
};