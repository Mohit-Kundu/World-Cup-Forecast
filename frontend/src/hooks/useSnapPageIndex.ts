import { RefObject, useEffect, useState } from 'react';

export function useSnapPageIndex(
  containerRef: RefObject<HTMLElement | null>,
  active: boolean
): number {
  const [pageIndex, setPageIndex] = useState(1);

  useEffect(() => {
    if (!active) return;

    const container = containerRef.current;
    if (!container) return;

    const updatePage = () => {
      const sections = container.querySelectorAll<HTMLElement>('[data-snap-section]');
      if (sections.length === 0) return;

      const viewportMid = container.scrollTop + container.clientHeight * 0.5;
      let bestIndex = 0;
      let bestDistance = Infinity;

      sections.forEach((section, index) => {
        const sectionMid = section.offsetTop + section.offsetHeight * 0.5;
        const distance = Math.abs(viewportMid - sectionMid);
        if (distance < bestDistance) {
          bestDistance = distance;
          bestIndex = index;
        }
      });

      setPageIndex(bestIndex + 1);
    };

    updatePage();
    container.addEventListener('scroll', updatePage, { passive: true });
    window.addEventListener('resize', updatePage);

    return () => {
      container.removeEventListener('scroll', updatePage);
      window.removeEventListener('resize', updatePage);
    };
  }, [containerRef, active]);

  return pageIndex;
}
