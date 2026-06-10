import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { PredictionsData, PredictionsStatus } from '../types';
import { normalizePredictions } from '../utils/safeData';

const API_URL = import.meta.env.VITE_API_URL || '';

const MIN_ITERATIONS = 10;
const MAX_ITERATIONS = 5000;
const DEFAULT_ITERATIONS = 200;

interface SimulationControlProps {
  onDataLoaded: (data: PredictionsData) => void;
}

export const SimulationControl: React.FC<SimulationControlProps> = ({ onDataLoaded }) => {
  const [status, setStatus] = useState<PredictionsStatus | null>(null);
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
      const response = await axios.get<PredictionsStatus>(
        `${API_URL}/api/predictions/status`
      );
      setStatus(response.data);

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
    <div className="rounded-lg border border-muted/30 bg-surface p-4 md:p-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-lg font-medium text-primary">Simulation Control</h2>
          <p className="mt-1 text-sm text-muted">
            {status?.has_predictions
              ? `Using pipeline results (${status.n_simulations.toLocaleString()} simulations)`
              : 'No predictions loaded. Run simulation or check pipeline output.'}
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="flex items-center gap-2">
            <label htmlFor="iterations" className="text-sm text-muted">
              Iterations:
            </label>
            <input
              id="iterations"
              type="number"
              min={MIN_ITERATIONS}
              max={MAX_ITERATIONS}
              value={iterations}
              onChange={(e) => setIterations(Number(e.target.value))}
              disabled={simulating}
              className="w-24 rounded-md border border-muted/50 bg-background px-3 py-1.5 text-sm text-primary focus:border-gold focus:outline-none disabled:opacity-50"
            />
          </div>

          <button
            onClick={runSimulation}
            disabled={simulating || loading}
            className="relative rounded-md bg-gold px-4 py-2 text-sm font-medium text-black transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {simulating ? (
              <span className="flex items-center gap-2">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-black/30 border-t-black" />
                Running...
              </span>
            ) : dataLoaded ? (
              'Re-run Simulation'
            ) : (
              'Run Simulation'
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="mt-4 rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {simulating && (
        <div className="mt-4">
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted/20">
            <div className="h-full animate-pulse rounded-full bg-gold" />
          </div>
          <p className="mt-2 text-xs text-muted">
            Running {iterations.toLocaleString()} Monte Carlo iterations...
            This may take a minute.
          </p>
        </div>
      )}
    </div>
  );
};