import React, { RefObject } from 'react';
import SnapPageIndicator from './SnapPageIndicator';

export const PAGE_SECTIONS = [
  { id: 'final', label: 'Final' },
  { id: 'knockout', label: 'Knockout' },
  { id: 'groups', label: 'Groups' },
  { id: 'teams', label: 'Teams' },
] as const;

interface SectionNavbarProps {
  containerRef: RefObject<HTMLElement | null>;
  activeIndex: number;
}

const SectionNavbar: React.FC<SectionNavbarProps> = ({ containerRef, activeIndex }) => {
  const scrollToSection = (index: number) => {
    const container = containerRef.current;
    if (!container) return;

    const sections = container.querySelectorAll<HTMLElement>('[data-snap-section]');
    const section = sections[index];
    if (!section) return;

    container.scrollTo({ top: section.offsetTop, behavior: 'smooth' });
  };

  return (
    <nav
      className="mb-4 flex shrink-0 items-center justify-between gap-4 border-b border-muted/20 pb-4"
      aria-label="Page sections"
    >
      <div className="flex min-w-0 flex-nowrap gap-1 overflow-x-auto scrollbar-hide">
        {PAGE_SECTIONS.map((section, index) => {
          const isActive = activeIndex === index + 1;

          return (
            <button
              key={section.id}
              type="button"
              onClick={() => scrollToSection(index)}
              aria-current={isActive ? 'page' : undefined}
              className={`shrink-0 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
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
      <SnapPageIndicator current={activeIndex} total={PAGE_SECTIONS.length} />
    </nav>
  );
};

export default SectionNavbar;
