import React, { RefObject, useMemo } from 'react';
import SnapPageIndicator from './SnapPageIndicator';

const MONITOR_SECTIONS = [
  { id: 'final', label: 'Final' },
  { id: 'knockout', label: 'Knockout' },
  { id: 'groups', label: 'Groups' },
  { id: 'teams', label: 'Teams' },
] as const;

const LAPTOP_SECTIONS = [
  { id: 'final', label: 'Final' },
  { id: 'wrapped', label: 'Wrapped' },
  { id: 'knockout', label: 'Knockout' },
  { id: 'groups', label: 'Groups' },
  { id: 'teams', label: 'Teams' },
] as const;

export const PAGE_SECTIONS = MONITOR_SECTIONS;

interface SectionNavbarProps {
  containerRef: RefObject<HTMLElement | null>;
  activeIndex: number;
  isMonitor: boolean;
}

const SectionNavbar: React.FC<SectionNavbarProps> = ({
  containerRef,
  activeIndex,
  isMonitor,
}) => {
  const sections = useMemo(
    () => (isMonitor ? MONITOR_SECTIONS : LAPTOP_SECTIONS),
    [isMonitor]
  );

  const scrollToSection = (index: number) => {
    const container = containerRef.current;
    if (!container) return;

    const snapSections = container.querySelectorAll<HTMLElement>('[data-snap-section]');
    const section = snapSections[index];
    if (!section) return;

    container.scrollTo({ top: section.offsetTop, behavior: 'smooth' });
  };

  return (
    <nav
      className="mb-1.5 flex shrink-0 items-center justify-between gap-2 border-b border-muted/20 pb-2 2xl:mb-4 2xl:gap-4 2xl:pb-4"
      aria-label="Page sections"
    >
      <div className="flex min-w-0 flex-nowrap gap-1 overflow-x-auto scrollbar-hide">
        {sections.map((section, index) => {
          const isActive = activeIndex === index + 1;

          return (
            <button
              key={section.id}
              type="button"
              onClick={() => scrollToSection(index)}
              aria-current={isActive ? 'page' : undefined}
              className={`shrink-0 rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors md:px-3 ${
                isActive
                  ? 'bg-gold/15 text-gold'
                  : 'text-muted hover:bg-surface hover:text-primary'
              }`}
            >
              {section.label}
            </button>
          );
        })}
      </div>
      <SnapPageIndicator current={activeIndex} total={sections.length} />
    </nav>
  );
};

export default SectionNavbar;
