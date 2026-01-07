(() => {
    const container = document.getElementById('hero-canvas');
    if (!container || typeof window.p5 === 'undefined') {
        return;
    }

    const seed = 15421;
    const palette = ['#3d5afe', '#69c9ff', '#35d6b4', '#ff7a6b'];
    const reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const measureCanvas = () => {
        const hero = container.closest('.hero');
        const rect = (hero || container).getBoundingClientRect();
        const width = Math.max(320, Math.floor(rect.width));
        const height = Math.max(260, Math.floor(rect.height || 360));
        return { width, height };
    };

    new p5((p) => {
        let particles = [];
        let center;
        let baseCenter;
        let targetCenter;
        let pointerActive = false;
        let particleCount = 900;

        const flowScale = 0.007;
        const driftSpeed = 1.05;
        const pulseStrength = 0.6;
        const trailAlpha = 12;
        const lineWeight = 0.9;

        const initializeSystem = () => {
            p.randomSeed(seed);
            p.noiseSeed(seed);

            baseCenter = p.createVector(p.width * 0.52, p.height * 0.56);
            center = baseCenter.copy();
            targetCenter = baseCenter.copy();
            const targetCount = Math.floor((p.width * p.height) / 1400);
            particleCount = Math.min(1300, Math.max(520, targetCount));

            particles = [];
            for (let i = 0; i < particleCount; i += 1) {
                particles.push(new Particle());
            }

            p.background(255, 248, 239);
        };

        const fieldAngle = (x, y, t) => {
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

        class Particle {
            constructor() {
                this.reset();
            }

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
            }

            update() {
            const t = p.frameCount * 0.0038;
            const angle = fieldAngle(this.pos.x, this.pos.y, t);
                const velocity = p5.Vector.fromAngle(angle).mult(driftSpeed);
                const dx = this.pos.x - center.x;
                const dy = this.pos.y - center.y;
                const distNorm = Math.sqrt(dx * dx + dy * dy) / p.width;
                const pressure = Math.sin(t * 1.4 + distNorm * 6.0) * (0.35 + pulseStrength * 0.45);
                const pressureVec = p5.Vector.sub(center, this.pos).normalize().mult(pressure);
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
            }

            render() {
                const c = p.color(palette[this.colorIndex]);
                c.setAlpha(trailAlpha);
                p.stroke(c);
                p.strokeWeight(Math.max(0.2, lineWeight + this.weightJitter));
                p.line(this.prev.x, this.prev.y, this.pos.x, this.pos.y);
            }
        }

        p.setup = () => {
            const { width, height } = measureCanvas();
            const canvas = p.createCanvas(width, height);
            canvas.parent(container);
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

            p.noStroke();
            p.fill(255, 248, 239, 14);
            p.rect(0, 0, p.width, p.height);

            for (let i = 0; i < particles.length; i += 1) {
                particles[i].update();
                particles[i].render();
            }
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

        p.mouseMoved = () => {
            pointerActive = true;
            targetCenter = p.createVector(p.mouseX, p.mouseY);
        };

        p.touchMoved = () => {
            pointerActive = true;
            targetCenter = p.createVector(p.mouseX, p.mouseY);
            return false;
        };

        p.mouseOut = () => {
            pointerActive = false;
        };
    });
})();
