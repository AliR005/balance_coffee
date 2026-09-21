export interface VideoStep {
  title: string;
  atSec: number;
}

/** Индекс текущего шага ролика по прошедшим секундам (зациклено на durationSec). */
export function activeStepIndex(
  elapsedSec: number,
  steps: VideoStep[],
  durationSec: number,
): number {
  if (steps.length === 0 || durationSec <= 0) return -1;
  const t = ((elapsedSec % durationSec) + durationSec) % durationSec;
  let active = 0;
  steps.forEach((s, i) => {
    if (s.atSec <= t) active = i;
  });
  return active;
}
