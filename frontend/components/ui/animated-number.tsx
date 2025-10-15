'use client';

import * as React from 'react';

interface AnimatedNumberProps {
  value: number;
  className?: string;
  duration?: number;
}

export function AnimatedNumber({ value, className = '', duration = 500 }: AnimatedNumberProps) {
  const [displayValue, setDisplayValue] = React.useState(0);
  const [prevValue, setPrevValue] = React.useState(0);

  React.useEffect(() => {
    if (value === prevValue) return;

    const startValue = displayValue;
    const endValue = value;
    const startTime = Date.now();
    let frameId: number;

    const animate = () => {
      const now = Date.now();
      const progress = Math.min((now - startTime) / duration, 1);

      // Easing function for smooth animation
      const easeOutQuad = (t: number) => t * (2 - t);
      const currentValue = Math.floor(startValue + (endValue - startValue) * easeOutQuad(progress));

      setDisplayValue(currentValue);

      if (progress < 1) {
        frameId = requestAnimationFrame(animate);
      } else {
        setPrevValue(value);
      }
    };

    frameId = requestAnimationFrame(animate);

    return () => cancelAnimationFrame(frameId);
  }, [value, prevValue, duration]);

  return <span className={className}>{displayValue}</span>;
}
