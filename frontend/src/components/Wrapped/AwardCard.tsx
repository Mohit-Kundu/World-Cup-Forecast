import FlagImage from '../FlagImage';
import { getAwardCardIcon } from './awardCardIcons';
import { AwardCard as AwardCardType } from './awardCards';

interface AwardCardProps {
  card: AwardCardType;
  className?: string;
  variant?: 'default' | 'laptop';
}

function AwardCard({ card, className, variant = 'default' }: AwardCardProps) {
  const isGroupCard = card.teams.length > 1;
  const Icon = getAwardCardIcon(card.id);
  const isLaptop = variant === 'laptop';

  const statsBlock = (
    <div>
      <p
        className="m-0 text-[30px] font-medium leading-none"
        style={{ color: card.accentColor }}
      >
        {card.bigNumber}
      </p>
      <p
        className={`m-0 mt-0.5 text-white/55 ${isLaptop ? 'text-sm' : 'text-[11px]'}`}
      >
        {card.statLabel}
      </p>
    </div>
  );

  const groupFlagClass = isLaptop
    ? 'h-7 w-[42px] shrink-0 rounded-sm object-cover ring-1 ring-white/20'
    : 'h-4 w-6 shrink-0 rounded-sm object-cover ring-1 ring-white/20';
  const teamFlagClass = isLaptop
    ? 'h-8 w-12 shrink-0 rounded-sm object-cover ring-1 ring-white/20'
    : 'h-5 w-[30px] shrink-0 rounded-sm object-cover ring-1 ring-white/20';

  const flagsBlock = (
    <div className={`flex items-center ${isLaptop ? 'gap-2' : 'gap-1.5'}`}>
      {isGroupCard ? (
        card.teams.map((team) => (
          <FlagImage key={team} team={team} className={groupFlagClass} />
        ))
      ) : (
        <>
          <FlagImage team={card.teams[0]} className={teamFlagClass} />
          {card.teamName && (
            <p
              className={`m-0 font-medium text-[#F1EFE8] ${isLaptop ? 'text-lg' : 'text-[14px]'}`}
            >
              {card.teamName}
            </p>
          )}
        </>
      )}
    </div>
  );

  const insightBlock = (
    <p
      className={`m-0 leading-snug text-white/55 ${isLaptop ? 'text-lg' : 'text-sm'}`}
    >
      {card.insight}
    </p>
  );

  return (
    <div className={`box-border h-full min-h-0 ${className ?? 'w-[280px] shrink-0'}`}>
      <div
        style={{ background: card.bgColor }}
        className={`award-card box-border flex h-full min-h-0 flex-col rounded-xl border border-white/10 ${
          isLaptop ? 'px-[18px] py-5' : 'p-[18px]'
        } ${isLaptop ? 'justify-start' : 'justify-between gap-2'}`}
      >
      <div className={`flex flex-col ${isLaptop ? 'min-h-0 flex-1 gap-2' : 'gap-2'}`}>
        <div className="flex items-end justify-between gap-2">
          <p
            className={`m-0 font-medium uppercase tracking-widest ${isLaptop ? 'text-xs' : 'text-[10px]'}`}
            style={{ color: card.accentColor }}
          >
            {card.label}
          </p>
          <Icon
            className={`shrink-0 ${isLaptop ? 'h-9 w-9' : 'h-6 w-6'}`}
            style={{ color: card.accentColor }}
            strokeWidth={1.75}
          />
        </div>

        <div className="h-px bg-white/10" />

        {card.badgeLabel && (
          <span
            className="self-start rounded px-2 py-0.5 text-[10px] font-medium"
            style={{
              background: card.badgeColor,
              color: card.badgeTextColor,
            }}
          >
            {card.badgeLabel}
          </span>
        )}

        {isLaptop && (
          <>
            <div className="mt-2 flex flex-col gap-3">
              {statsBlock}
              {flagsBlock}
            </div>
            <div className="mt-auto">{insightBlock}</div>
          </>
        )}
      </div>

      {!isLaptop && statsBlock}

      {!isLaptop && (
        <>
          {flagsBlock}
          {insightBlock}
        </>
      )}
      </div>
    </div>
  );
}

export default AwardCard;
