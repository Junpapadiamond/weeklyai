"use client";

import { useEffect, useRef } from "react";
import type P5 from "p5";

export default function HeroCanvas() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let p5Instance: P5 | null = null;
    let mounted = true;

    const setupSketch = async () => {
      const p5Module = await import("p5");
      const P5Constructor = p5Module.default;

      if (!mounted || !containerRef.current) {
        return;
      }

      const seed = 15421;
      const reduceMotion =
        window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

      const isDarkMode = () => document.documentElement.getAttribute("data-theme") === "dark";
      const lightPalette = ["#E61E4D", "#FFB400", "#222222", "#9CA3AF"];
      const darkPalette = ["#D61F3D", "#FFB400", "#F7F7F7", "#9E9E9E"];
      const lightBg: [number, number, number] = [255, 255, 255];
      const darkBg: [number, number, number] = [11, 11, 11];

      const getPalette = () => (isDarkMode() ? darkPalette : lightPalette);
      const getBgColor = () => (isDarkMode() ? darkBg : lightBg);

      p5Instance = new P5Constructor((p) => {
        let particles: Array<{
          pos: P5.Vector;
          prev: P5.Vector;
          colorIndex: number;
          life: number;
          weightJitter: number;
          reset: () => void;
          update: () => void;
          render: () => void;
        }> = [];

        let center = p.createVector(0, 0);
        let baseCenter = p.createVector(0, 0);
        let targetCenter = p.createVector(0, 0);
        let pointerActive = false;
        let palette = getPalette();

        const flowScale = 0.007;
        const driftSpeed = 1.05;
        const pulseStrength = 0.6;
        const trailAlpha = 10;
        const lineWeight = 0.85;

        const measureCanvas = () => {
          const container = containerRef.current;
          const hero = container?.closest(".hero");
          const rect = (hero || container)?.getBoundingClientRect();
          const width = Math.max(320, Math.floor(rect?.width || 960));
          const height = Math.max(260, Math.floor(rect?.height || 360));
          return { width, height };
        };

        const fieldAngle = (x: number, y: number, t: number) => {
          const baseX = x * flowScale;
          const baseY = y * flowScale;
          const n1 = p.noise(baseX, baseY, t);
          const n2 = p.noise(baseX * 1.7 + 120, baseY * 1.7 - 60, t * 1.25);
          const dx = x - center.x;
          const dy = y - center.y;
          const distNorm = Math.sqrt(dx * dx + dy * dy) / p.width;
          const tide = Math.sin((distNorm * 12.0 + t * 1.6) * p.TWO_PI) * pulseStrength;
          const swirl = Math.atan2(dy, dx) * 0.28;
          return (n1 * 2.0 + n2 * 0.9) * p.TWO_PI + swirl + tide;
        };

        const initializeSystem = () => {
          p.randomSeed(seed);
          p.noiseSeed(seed);
          palette = getPalette();

          baseCenter = p.createVector(p.width * 0.52, p.height * 0.56);
          center = baseCenter.copy();
          targetCenter = baseCenter.copy();

          const targetCount = Math.floor((p.width * p.height) / 1400);
          const particleCount = Math.min(1300, Math.max(520, targetCount));

          particles = [];
          for (let i = 0; i < particleCount; i += 1) {
            const particle = {
              pos: p.createVector(0, 0),
              prev: p.createVector(0, 0),
              colorIndex: 0,
              life: 0,
              weightJitter: 0,
              reset() {
                const edge = Math.floor(p.random(4));
                if (edge === 0) {
                  this.pos = p.createVector(p.random(p.width), -10);
                } else if (edge === 1) {
                  this.pos = p.createVector(p.width + 10, p.random(p.height));
                } else if (edge === 2) {
                  this.pos = p.createVector(p.random(p.width), p.height + 10);
                } else {
                  this.pos = p.createVector(-10, p.random(p.height));
                }
                this.prev = this.pos.copy();
                this.colorIndex = Math.floor(p.random(palette.length));
                this.life = Math.floor(p.random(160, 280));
                this.weightJitter = p.random(-0.2, 0.3);
              },
              update() {
                const t = p.frameCount * 0.0038;
                const angle = fieldAngle(this.pos.x, this.pos.y, t);
                const velocity = P5Constructor.Vector.fromAngle(angle).mult(driftSpeed);

                const dx = this.pos.x - center.x;
                const dy = this.pos.y - center.y;
                const distNorm = Math.sqrt(dx * dx + dy * dy) / p.width;
                const pressure = Math.sin(t * 1.4 + distNorm * 6.0) * (0.35 + pulseStrength * 0.45);
                const pressureVec = P5Constructor.Vector.sub(center, this.pos)
                  .normalize()
                  .mult(pressure);

                velocity.add(pressureVec);
                this.prev = this.pos.copy();
                this.pos.add(velocity);
                this.life -= 1;

                if (
                  this.pos.x < -20 ||
                  this.pos.x > p.width + 20 ||
                  this.pos.y < -20 ||
                  this.pos.y > p.height + 20 ||
                  this.life <= 0
                ) {
                  this.reset();
                }
              },
              render() {
                const c = p.color(palette[this.colorIndex]);
                c.setAlpha(trailAlpha);
                p.stroke(c);
                p.strokeWeight(Math.max(0.2, lineWeight + this.weightJitter));
                p.line(this.prev.x, this.prev.y, this.pos.x, this.pos.y);
              },
            };

            particle.reset();
            particles.push(particle);
          }

          const bg = getBgColor();
          p.background(bg[0], bg[1], bg[2]);
        };

        p.setup = () => {
          const { width, height } = measureCanvas();
          const canvas = p.createCanvas(width, height);
          canvas.parent(containerRef.current as Element);
          p.pixelDensity(1);
          p.frameRate(30);
          initializeSystem();

          if (reduceMotion) {
            p.noLoop();
          }
        };

        p.draw = () => {
          if (pointerActive) {
            center.lerp(targetCenter, 0.06);
          } else {
            center.lerp(baseCenter, 0.03);
          }

          const bg = getBgColor();
          p.noStroke();
          p.fill(bg[0], bg[1], bg[2], 12);
          p.rect(0, 0, p.width, p.height);

          for (const particle of particles) {
            particle.update();
            particle.render();
          }
        };

        p.mouseMoved = () => {
          pointerActive = true;
          targetCenter = p.createVector(p.mouseX, p.mouseY);
        };

        p.windowResized = () => {
          const { width, height } = measureCanvas();
          p.resizeCanvas(width, height);
          initializeSystem();
          if (reduceMotion) {
            p.noLoop();
            p.redraw();
          }
        };

        const observer = new MutationObserver((mutations) => {
          for (const mutation of mutations) {
            if (mutation.attributeName === "data-theme") {
              initializeSystem();
            }
          }
        });

        observer.observe(document.documentElement, { attributes: true });
      });
    };

    void setupSketch();

    return () => {
      mounted = false;
      p5Instance?.remove();
      p5Instance = null;
    };
  }, []);

  return <div id="hero-canvas" ref={containerRef} className="hero-canvas" aria-hidden="true" />;
}
