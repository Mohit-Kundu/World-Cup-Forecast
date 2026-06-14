import React, { useRef, useCallback, useEffect } from 'react';
import { PredictedFinal, TeamStats } from '../../types';
import FlagImage from '../FlagImage';
import FinalOutcomeBar from './FinalOutcomeBar';
import FinalTeamStats from './FinalTeamStats';
import { FINAL_WINNER_COLOR, FINAL_WINNER_TEXT_GLOW } from './finalColors';

const FINAL_CARD_CLASS =
  'award-card award-card--gold-shine box-border rounded-xl border border-muted/20 bg-surface';

interface PredictedFinalCardProps {
  predictedFinal: PredictedFinal;
  teamStats: Record<string, TeamStats>;
  qualifyProbs: Record<string, number>;
  championProbs: Record<string, number>;
}

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  color: string;
  rotation: number;
  rotationSpeed: number;
  shape: 'rect' | 'circle' | 'ribbon';
  opacity: number;
  gravity: number;
}

const CONFETTI_COLORS = [
  FINAL_WINNER_COLOR,
  '#FAC775',
  '#FFFFFF',
  '#A3E635',
  '#38BDF8',
  '#F472B6',
  '#FB923C',
];

function spawnBurst(
  particles: Particle[],
  originX: number,
  originY: number,
  angleMin: number,
  angleMax: number,
  count: number,
  mirrorX = false
) {
  for (let i = 0; i < count; i++) {
    const angle = angleMin + Math.random() * (angleMax - angleMin);
    const speed = 2 + Math.random() * 5;
    const shape = (['rect', 'circle', 'ribbon'] as const)[Math.floor(Math.random() * 3)];
    const direction = mirrorX ? Math.PI - angle : angle;

    particles.push({
      x: originX + (Math.random() - 0.5) * 24,
      y: originY + (Math.random() - 0.5) * 16,
      vx: Math.cos(direction) * speed * (Math.random() * 0.8 + 0.6),
      vy: Math.sin(direction) * speed - 2,
      size: 4 + Math.random() * 6,
      color: CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)],
      rotation: Math.random() * Math.PI * 2,
      rotationSpeed: (Math.random() - 0.5) * 0.3,
      shape,
      opacity: 1,
      gravity: 0.12 + Math.random() * 0.08,
    });
  }
}

const CONFETTI_FAN_ROTATION = -Math.PI / 4;

function spawnConfetti(canvas: HTMLCanvasElement): Particle[] {
  const particles: Particle[] = [];
  const perCorner = 30;
  const topY = canvas.height * 0.08;
  const insetX = canvas.width * 0.06;
  const angleMin = Math.PI * 0.2 + CONFETTI_FAN_ROTATION;
  const angleMax = Math.PI * 0.8 + CONFETTI_FAN_ROTATION;

  // Left top corner — fan down and right
  spawnBurst(particles, insetX, topY, angleMin, angleMax, perCorner);
  // Right top corner — fan down and left
  spawnBurst(particles, canvas.width - insetX, topY, angleMin, angleMax, perCorner, true);

  return particles;
}

function drawParticle(ctx: CanvasRenderingContext2D, p: Particle) {
  ctx.save();
  ctx.globalAlpha = p.opacity;
  ctx.fillStyle = p.color;
  ctx.translate(p.x, p.y);
  ctx.rotate(p.rotation);

  if (p.shape === 'circle') {
    ctx.beginPath();
    ctx.arc(0, 0, p.size / 2, 0, Math.PI * 2);
    ctx.fill();
  } else if (p.shape === 'ribbon') {
    ctx.fillRect(-p.size * 1.5, -p.size / 4, p.size * 3, p.size / 2);
  } else {
    ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size);
  }

  ctx.restore();
}

const PredictedFinalCard: React.FC<PredictedFinalCardProps> = ({
  predictedFinal,
  teamStats,
  qualifyProbs,
  championProbs,
}) => {
  const { home_team, away_team, winner, runner_up, pairing_prob, winner_prob } = predictedFinal;

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animFrameRef = useRef<number | null>(null);
  const particlesRef = useRef<Particle[]>([]);

  const stopConfetti = useCallback(() => {
    if (animFrameRef.current !== null) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      ctx?.clearRect(0, 0, canvas.width, canvas.height);
    }
    particlesRef.current = [];
  }, []);

  const runConfetti = useCallback(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    if (animFrameRef.current !== null) {
      cancelAnimationFrame(animFrameRef.current);
    }

    particlesRef.current = spawnConfetti(canvas);

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particlesRef.current = particlesRef.current.filter((p) => p.opacity > 0.02);

      for (const p of particlesRef.current) {
        p.x += p.vx;
        p.y += p.vy;
        p.vy += p.gravity;
        p.vx *= 0.99;
        p.rotation += p.rotationSpeed;
        p.opacity -= 0.012;
        drawParticle(ctx, p);
      }

      if (particlesRef.current.length > 0) {
        animFrameRef.current = requestAnimationFrame(animate);
      } else {
        animFrameRef.current = null;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    };

    animFrameRef.current = requestAnimationFrame(animate);
  }, []);

  useEffect(() => () => stopConfetti(), [stopConfetti]);

  if (!home_team || !away_team) {
    return (
      <section>
        <h2 className="mb-4 text-sm font-medium text-primary">Predicted Final</h2>
        <div className={`${FINAL_CARD_CLASS} px-8 py-6 text-center text-xs text-muted`}>
          No final prediction available
        </div>
      </section>
    );
  }

  return (
    <section>
      <div className="mb-4">
        <h2 className="text-sm font-medium text-primary">Predicted Final</h2>
        <p className="mt-1 text-xs text-muted">
          Most common final pairing across simulations ({(pairing_prob * 100).toFixed(1)}% of runs).
        </p>
      </div>

      <div
        className="relative"
        onMouseEnter={runConfetti}
        onMouseLeave={stopConfetti}
      >
        <div className={`${FINAL_CARD_CLASS} relative z-0 px-4 py-5 sm:px-6 md:px-8 md:pt-6 md:pb-3`}>
          <div className="space-y-6">
            <div className="text-center">
              <div className="flex items-center justify-center gap-2 text-xl leading-none sm:gap-3 sm:text-2xl md:text-3xl">
                <p
                  className="font-black uppercase tracking-[0.25em]"
                  style={{ color: FINAL_WINNER_COLOR, textShadow: FINAL_WINNER_TEXT_GLOW }}
                >
                  Winner!
                </p>
                <FlagImage
                  team={winner}
                  srcWidth={320}
                  loading="eager"
                  className="h-6 w-9 shrink-0 rounded-sm object-cover ring-1 ring-[#FAC775]/40 sm:h-7 sm:w-10"
                />
              </div>
            </div>

            <div className="space-y-3">
              <FinalOutcomeBar
                leftTeam={winner}
                rightTeam={runner_up}
                leftProb={winner_prob}
                rightProb={1 - winner_prob}
                leftIsWinner
                rightIsWinner={false}
              />

              <FinalTeamStats
                leftTeam={winner}
                rightTeam={runner_up}
                leftIsWinner
                rightIsWinner={false}
                teamStats={teamStats}
                qualifyProbs={qualifyProbs}
                championProbs={championProbs}
              />
            </div>
          </div>
        </div>

        <canvas
          ref={canvasRef}
          width={600}
          height={400}
          className="pointer-events-none absolute inset-0 z-10 h-full w-full rounded-xl"
          aria-hidden
        />
      </div>
    </section>
  );
};

export default PredictedFinalCard;
