import React, { useEffect, useMemo, useState } from 'react';
import { TableDataItem, TeamStats } from '../../types';
import { getTeamStats } from '../../utils/safeData';
import { CONFEDERATIONS, WC2026_GROUPS } from '../../utils/teams';
import FlagTooltip from '../FlagTooltip';

interface ProbabilityTableProps {
  data: TableDataItem[];
  teamStats: Record<string, TeamStats>;
}

type SortKey = keyof TableDataItem;
type SortOrder = 'asc' | 'desc';

const PAGE_SIZE = 10;
const GROUP_OPTIONS = ['', ...Object.keys(WC2026_GROUPS)];

const SORTABLE_COLUMNS: { key: SortKey; label: string }[] = [
  { key: 'rank', label: '#' },
  { key: 'team', label: 'Team' },
  { key: 'qualifyProb', label: 'Qualify' },
  { key: 'championProb', label: 'Champ' },
  { key: 'elo', label: 'Elo' },
  { key: 'form', label: 'Form' },
  { key: 'attack', label: 'Atk' },
  { key: 'defense', label: 'Def' },
];

const inputClass =
  'h-8 rounded-md border border-muted/40 bg-background px-2 py-1 text-xs text-primary placeholder:text-muted/70 focus:border-gold focus:outline-none';
const btnClass =
  'inline-flex h-8 items-center justify-center rounded-md border border-muted/40 px-2 text-xs text-primary transition-colors hover:border-muted/60 disabled:cursor-not-allowed disabled:opacity-40';

const ProbabilityTable: React.FC<ProbabilityTableProps> = ({ data, teamStats }) => {
  const [sortKey, setSortKey] = useState<SortKey>('championProb');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [groupFilter, setGroupFilter] = useState('');
  const [confederationFilter, setConfederationFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);

  useEffect(() => {
    setPage(1);
  }, [groupFilter, confederationFilter, searchQuery, sortKey, sortOrder]);

  const filteredData = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    return data.filter((row) => {
      if (groupFilter && row.group !== groupFilter) return false;
      if (confederationFilter && row.confederation !== confederationFilter) return false;
      if (query && !row.team.toLowerCase().includes(query)) return false;
      return true;
    });
  }, [data, groupFilter, confederationFilter, searchQuery]);

  const sortedData = useMemo(() => {
    return [...filteredData].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];

      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortOrder === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
      }

      return sortOrder === 'asc'
        ? (aVal as number) - (bVal as number)
        : (bVal as number) - (aVal as number);
    });
  }, [filteredData, sortKey, sortOrder]);

  const rankedData = useMemo(
    () => sortedData.map((row, index) => ({ ...row, rank: index + 1 })),
    [sortedData]
  );

  const totalPages = Math.max(1, Math.ceil(rankedData.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const pageStart = (safePage - 1) * PAGE_SIZE;
  const pageData = rankedData.slice(pageStart, pageStart + PAGE_SIZE);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder(key === 'team' || key === 'form' ? 'asc' : 'desc');
    }
  };

  const sortIndicator = (key: SortKey) => {
    if (sortKey !== key) return '';
    return sortOrder === 'asc' ? ' ↑' : ' ↓';
  };

  const thClass = (key: SortKey) =>
    `cursor-pointer select-none px-2 py-2 text-left text-[9px] font-normal uppercase tracking-wider transition-colors ${
      sortKey === key ? 'text-primary' : 'text-muted/70 hover:text-primary'
    }`;

  return (
    <div className="rounded-lg border border-muted/20 bg-surface px-6 py-4">
      <div className="mb-4 grid grid-cols-1 items-center gap-3 sm:grid-cols-[1fr_auto]">
        <div className="min-w-0">
          <h3 className="text-xs font-medium uppercase tracking-widest text-muted">All teams</h3>
          <p className="mt-1 text-[10px] text-muted/70">
            {rankedData.length === 0
              ? 'No teams match filters'
              : `Showing ${pageStart + 1}–${Math.min(pageStart + PAGE_SIZE, rankedData.length)} of ${rankedData.length}`}
          </p>
        </div>

        <div className="flex flex-nowrap items-center justify-end gap-1.5">
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={rankedData.length === 0 || safePage <= 1}
            className={btnClass}
            aria-label="Previous page"
          >
            ‹
          </button>
          <span className="inline-flex h-8 min-w-[3.5rem] items-center justify-center text-xs tabular-nums text-primary">
            {safePage} / {totalPages}
          </span>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={rankedData.length === 0 || safePage >= totalPages}
            className={btnClass}
            aria-label="Next page"
          >
            ›
          </button>
        </div>
      </div>

      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <label className="flex items-center gap-2 text-[10px] text-muted/70">
            Group
            <select
              value={groupFilter}
              onChange={(e) => setGroupFilter(e.target.value)}
              className={inputClass}
            >
              <option value="">All</option>
              {GROUP_OPTIONS.filter(Boolean).map((group) => (
                <option key={group} value={group}>
                  {group}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-2 text-[10px] text-muted/70">
            Confederation
            <select
              value={confederationFilter}
              onChange={(e) => setConfederationFilter(e.target.value)}
              className={inputClass}
            >
              <option value="">All</option>
              {CONFEDERATIONS.map((conf) => (
                <option key={conf} value={conf}>
                  {conf}
                </option>
              ))}
            </select>
          </label>
        </div>
        <input
          type="search"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search teams..."
          aria-label="Search teams"
          className={`w-full sm:ml-auto sm:w-44 sm:shrink-0 ${inputClass}`}
        />
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-muted/20">
              {SORTABLE_COLUMNS.map((col, index) => (
                <React.Fragment key={col.key}>
                  {index === 1 && (
                    <th className="px-2 py-2 text-left text-[9px] font-normal uppercase tracking-wider text-muted/70">
                      Flag
                    </th>
                  )}
                  <th className={thClass(col.key)} onClick={() => handleSort(col.key)}>
                    {col.label}
                    {sortIndicator(col.key)}
                  </th>
                </React.Fragment>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageData.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-2 py-8 text-center text-xs text-muted/70">
                  No teams to display
                </td>
              </tr>
            ) : (
              pageData.map((row) => (
                <tr key={row.team} className="border-b border-muted/10 hover:bg-background">
                  <td className="px-2 py-2 font-normal tabular-nums text-primary">{row.rank}</td>
                  <td className="px-2 py-2">
                    <FlagTooltip team={row.team} stats={getTeamStats(teamStats, row.team)} />
                  </td>
                  <td className="px-2 py-2 font-medium text-primary">{row.team}</td>
                  <td className="px-2 py-2 font-normal tabular-nums text-primary">
                    {(row.qualifyProb * 100).toFixed(2)}%
                  </td>
                  <td className="px-2 py-2 font-normal tabular-nums text-gold">
                    {(row.championProb * 100).toFixed(2)}%
                  </td>
                  <td className="px-2 py-2 font-normal tabular-nums text-primary">{row.elo}</td>
                  <td className="px-2 py-2 font-normal text-primary">{row.form}</td>
                  <td className="px-2 py-2 font-normal tabular-nums text-primary">
                    {row.attack.toFixed(2)}
                  </td>
                  <td className="px-2 py-2 font-normal tabular-nums text-primary">
                    {row.defense.toFixed(2)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ProbabilityTable;
