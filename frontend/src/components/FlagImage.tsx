import React, { useState } from 'react';
import { getFlagUrl, getIsoCode } from '../utils/flags';

interface FlagImageProps {
  team: string;
  className?: string;
}

const FlagImage: React.FC<FlagImageProps> = ({
  team,
  className = 'h-3.5 w-5 rounded-sm object-cover ring-1 ring-muted/40',
}) => {
  const [error, setError] = useState(false);

  if (error) {
    return (
      <span
        className="inline-flex h-3.5 w-5 items-center justify-center rounded-sm bg-background text-[8px] font-medium uppercase text-muted ring-1 ring-muted/40"
        title={team}
      >
        {getIsoCode(team)}
      </span>
    );
  }

  return (
    <img
      src={getFlagUrl(team)}
      alt={`${team} flag`}
      title={team}
      className={className}
      loading="lazy"
      onError={() => setError(true)}
    />
  );
};

export default FlagImage;
