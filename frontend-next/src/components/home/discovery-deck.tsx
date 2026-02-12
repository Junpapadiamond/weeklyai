"use client";

import { PointerEvent, TouchEvent, useEffect, useRef, useState } from "react";
import type { Product } from "@/types/api";
import {
  cleanDescription,
  formatCategories,
  isValidWebsite,
  normalizeWebsite,
  productKey,
} from "@/lib/product-utils";

const SWIPED_KEY = "weeklyai_swiped";
const SWIPE_GUIDE_SEEN_KEY = "weeklyai_swipe_guide_seen";
const SWIPED_EXPIRY_DAYS = 7;
const SWIPE_THRESHOLD_TOUCH = 70;
const SWIPE_THRESHOLD_POINTER = 92;
const SWIPE_OUT_OFFSET_BASE = 620;
const SWIPE_EXIT_MS = 280;
const SWIPE_EXIT_MS_MIN = 190;
const SWIPE_RETURN_MS = 220;
const SWIPE_FEEDBACK_MIN = 24;
const SWIPE_TAP_THRESHOLD = 10;
const SWIPE_FLICK_MIN_DISTANCE_TOUCH = 34;
const SWIPE_FLICK_MIN_DISTANCE_POINTER = 46;
const SWIPE_FLICK_VELOCITY_TOUCH = 0.48;
const SWIPE_FLICK_VELOCITY_POINTER = 0.58;
const SWIPE_INERTIA_MIN_VELOCITY_TOUCH = 0.7;
const SWIPE_INERTIA_MIN_VELOCITY_POINTER = 0.82;
const SWIPE_INERTIA_VELOCITY_CAP_TOUCH = 1.9;
const SWIPE_INERTIA_VELOCITY_CAP_POINTER = 2.15;
const SWIPE_INERTIA_EXTRA_OFFSET_MAX = 360;
const SWIPE_INERTIA_DURATION_REDUCTION_MAX = 96;
const SWIPE_INERTIA_STRONG_THRESHOLD = 0.28;

type DiscoveryDeckProps = {
  products: Product[];
  onLike: (product: Product) => void;
};

type SwipedState = {
  keys: string[];
  timestamp: number;
};

type SwipeInput = {
  pointerType?: "touch" | "mouse" | "pen";
  velocityX?: number;
  deltaX?: number;
  deltaY?: number;
};

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function getSwipedProducts(): SwipedState {
  if (typeof window === "undefined") return { keys: [], timestamp: Date.now() };

  try {
    const stored = window.localStorage.getItem(SWIPED_KEY);
    if (!stored) return { keys: [], timestamp: Date.now() };

    const parsed = JSON.parse(stored) as SwipedState;
    const expiryMs = SWIPED_EXPIRY_DAYS * 24 * 60 * 60 * 1000;
    if (Date.now() - parsed.timestamp > expiryMs) {
      window.localStorage.removeItem(SWIPED_KEY);
      return { keys: [], timestamp: Date.now() };
    }

    return parsed;
  } catch {
    return { keys: [], timestamp: Date.now() };
  }
}

function saveSwipedProducts(data: SwipedState) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(SWIPED_KEY, JSON.stringify(data));
}

function shuffle<T>(arr: T[]): T[] {
  const cloned = [...arr];
  for (let i = cloned.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [cloned[i], cloned[j]] = [cloned[j], cloned[i]];
  }
  return cloned;
}

function createDeck(products: Product[]) {
  const swiped = getSwipedProducts();
  const filtered = products.filter((product) => {
    const key = productKey(product);
    return key && !swiped.keys.includes(key);
  });

  if (filtered.length === 0 && typeof window !== "undefined") {
    window.localStorage.removeItem(SWIPED_KEY);
  }

  const source = filtered.length ? filtered : [...products];
  const shuffled = shuffle(source);
  return {
    stack: shuffled.slice(0, 3),
    pool: shuffled.slice(3),
  };
}

export default function DiscoveryDeck({ products, onLike }: DiscoveryDeckProps) {
  const [deck, setDeck] = useState(() => createDeck(products));
  const [liked, setLiked] = useState(0);
  const [skipped, setSkipped] = useState(0);
  const [likeStreak, setLikeStreak] = useState(0);
  const [showSwipeGuide, setShowSwipeGuide] = useState(false);
  const [dragX, setDragX] = useState(0);
  const [dragY, setDragY] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [gestureInputType, setGestureInputType] = useState<"pointer" | "touch" | null>(null);
  const [swipeExitMs, setSwipeExitMs] = useState(SWIPE_EXIT_MS);
  const [swipeOutDirection, setSwipeOutDirection] = useState<"left" | "right" | null>(null);
  const [lastSwipeAction, setLastSwipeAction] = useState<"left" | "right" | null>(null);
  const [lastSwipeHadInertia, setLastSwipeHadInertia] = useState(false);
  const [showSwipeEcho, setShowSwipeEcho] = useState(false);
  const [showStreakBurst, setShowStreakBurst] = useState(false);
  const likeStreakRef = useRef(0);
  const dragStartX = useRef<number | null>(null);
  const dragStartY = useRef<number | null>(null);
  const dragPointerId = useRef<number | null>(null);
  const dragTouchId = useRef<number | null>(null);
  const lastClientX = useRef<number | null>(null);
  const lastClientY = useRef<number | null>(null);
  const lastMoveTs = useRef<number | null>(null);
  const velocityX = useRef(0);
  const activeGestureInput = useRef<"pointer" | "touch" | null>(null);
  const isSwipeOutRef = useRef(false);
  const swipeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const swipeEchoTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const streakBurstTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const stack = deck.stack;
  const pool = deck.pool;

  function dismissSwipeGuide() {
    setShowSwipeGuide(false);
    if (typeof window === "undefined") return;
    window.localStorage.setItem(SWIPE_GUIDE_SEEN_KEY, "1");
  }

  useEffect(() => {
    return () => {
      if (swipeTimerRef.current) {
        clearTimeout(swipeTimerRef.current);
      }
      if (swipeEchoTimerRef.current) {
        clearTimeout(swipeEchoTimerRef.current);
      }
      if (streakBurstTimerRef.current) {
        clearTimeout(streakBurstTimerRef.current);
      }
      isSwipeOutRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (window.localStorage.getItem(SWIPE_GUIDE_SEEN_KEY) === "1") return;
    const rafId = window.requestAnimationFrame(() => setShowSwipeGuide(true));
    return () => window.cancelAnimationFrame(rafId);
  }, []);

  function refill(nextStack: Product[], nextPool: Product[]) {
    const mergedStack = [...nextStack];
    const mergedPool = [...nextPool];

    while (mergedStack.length < 3 && mergedPool.length > 0) {
      const candidate = mergedPool.shift();
      if (candidate) mergedStack.push(candidate);
    }

    return { nextStack: mergedStack, nextPool: mergedPool };
  }

  function markSwiped(product: Product) {
    const key = productKey(product);
    if (!key) return;

    const swiped = getSwipedProducts();
    if (!swiped.keys.includes(key)) {
      swiped.keys.push(key);
      saveSwipedProducts(swiped);
    }
  }

  function swipe() {
    if (!stack.length) return;

    const [current, ...restStack] = stack;
    markSwiped(current);

    const { nextStack, nextPool } = refill(restStack, pool);
    setDeck({ stack: nextStack, pool: nextPool });
  }

  function resetDrag() {
    dragStartX.current = null;
    dragStartY.current = null;
    dragPointerId.current = null;
    dragTouchId.current = null;
    lastClientX.current = null;
    lastClientY.current = null;
    lastMoveTs.current = null;
    velocityX.current = 0;
    activeGestureInput.current = null;
    setGestureInputType(null);
    setIsDragging(false);
    if (!isSwipeOutRef.current) {
      setDragX(0);
      setDragY(0);
    }
  }

  function tryOpenCurrentWebsite() {
    if (typeof window === "undefined") return;
    const current = stack[0];
    if (!current) return;
    const website = normalizeWebsite(current.website);
    if (!isValidWebsite(website)) return;
    window.open(website, "_blank", "noopener,noreferrer");
  }

  function shouldIgnoreGestureStart(target: EventTarget | null) {
    return target instanceof Element && !!target.closest("a, button");
  }

  function resolveSwipePhysics(input?: SwipeInput) {
    const pointerType = input?.pointerType || "mouse";
    const isTouch = pointerType === "touch";
    const minVelocity = isTouch ? SWIPE_INERTIA_MIN_VELOCITY_TOUCH : SWIPE_INERTIA_MIN_VELOCITY_POINTER;
    const velocityCap = isTouch ? SWIPE_INERTIA_VELOCITY_CAP_TOUCH : SWIPE_INERTIA_VELOCITY_CAP_POINTER;
    const threshold = isTouch ? SWIPE_THRESHOLD_TOUCH : SWIPE_THRESHOLD_POINTER;
    const absVelocity = Math.abs(input?.velocityX || 0);
    const absDelta = Math.abs(input?.deltaX || dragX);
    const velocityRatio = clamp((absVelocity - minVelocity) / (velocityCap - minVelocity), 0, 1);
    const distanceRatio = clamp(absDelta / threshold, 0, 1.2);
    const inertiaStrength = clamp(velocityRatio * 0.8 + distanceRatio * 0.2, 0, 1);
    const extraOffset = Math.round(inertiaStrength * SWIPE_INERTIA_EXTRA_OFFSET_MAX);
    const exitMs = Math.round(
      clamp(
        SWIPE_EXIT_MS - inertiaStrength * SWIPE_INERTIA_DURATION_REDUCTION_MAX,
        SWIPE_EXIT_MS_MIN,
        SWIPE_EXIT_MS
      )
    );

    return {
      extraOffset,
      exitMs,
      inertiaStrength,
    };
  }

  function animateSwipe(direction: "left" | "right", input?: SwipeInput) {
    if (!stack.length || swipeOutDirection) return;
    if (showSwipeGuide) {
      dismissSwipeGuide();
    }
    const current = stack[0];
    const physics = resolveSwipePhysics(input);
    const exitOffset =
      typeof window === "undefined"
        ? SWIPE_OUT_OFFSET_BASE
        : Math.max(SWIPE_OUT_OFFSET_BASE, Math.round(window.innerWidth * 0.92)) + physics.extraOffset;
    const releaseDeltaY = input?.deltaY ?? dragY;
    const hadInertia = physics.inertiaStrength >= SWIPE_INERTIA_STRONG_THRESHOLD;
    isSwipeOutRef.current = true;
    setSwipeExitMs(physics.exitMs);
    setSwipeOutDirection(direction);
    setLastSwipeHadInertia(hadInertia);
    setLastSwipeAction(direction);
    setShowSwipeEcho(true);
    if (direction === "right") {
      setLiked((value) => value + 1);
      const nextStreak = likeStreakRef.current + 1;
      likeStreakRef.current = nextStreak;
      setLikeStreak(nextStreak);
      if (nextStreak >= 2) {
        if (streakBurstTimerRef.current) {
          clearTimeout(streakBurstTimerRef.current);
        }
        setShowStreakBurst(true);
        streakBurstTimerRef.current = setTimeout(() => {
          setShowStreakBurst(false);
          streakBurstTimerRef.current = null;
        }, 980);
      }
      onLike(current);
    } else {
      setSkipped((value) => value + 1);
      likeStreakRef.current = 0;
      setLikeStreak(0);
      setShowStreakBurst(false);
      if (streakBurstTimerRef.current) {
        clearTimeout(streakBurstTimerRef.current);
        streakBurstTimerRef.current = null;
      }
    }
    setIsDragging(false);
    setDragX(direction === "right" ? exitOffset : -exitOffset);
    setDragY(releaseDeltaY * (0.32 + physics.inertiaStrength * 0.08));

    if (swipeEchoTimerRef.current) {
      clearTimeout(swipeEchoTimerRef.current);
    }
    swipeEchoTimerRef.current = setTimeout(() => {
      setShowSwipeEcho(false);
      swipeEchoTimerRef.current = null;
    }, 820);

    if (swipeTimerRef.current) {
      clearTimeout(swipeTimerRef.current);
    }
    swipeTimerRef.current = setTimeout(() => {
      swipe();
      setDragX(0);
      setDragY(0);
      setSwipeExitMs(SWIPE_EXIT_MS);
      setSwipeOutDirection(null);
      isSwipeOutRef.current = false;
      dragStartX.current = null;
      dragStartY.current = null;
      dragPointerId.current = null;
      dragTouchId.current = null;
      lastClientX.current = null;
      lastClientY.current = null;
      lastMoveTs.current = null;
      velocityX.current = 0;
      activeGestureInput.current = null;
      setGestureInputType(null);
      swipeTimerRef.current = null;
    }, physics.exitMs);
  }

  function beginDrag(clientX: number, clientY: number, inputType: "pointer" | "touch") {
    activeGestureInput.current = inputType;
    setGestureInputType(inputType);
    dragStartX.current = clientX;
    dragStartY.current = clientY;
    lastClientX.current = clientX;
    lastClientY.current = clientY;
    lastMoveTs.current = Date.now();
    velocityX.current = 0;
    setIsDragging(true);
    setDragX(0);
    setDragY(0);
  }

  function updateDrag(clientX: number, clientY: number) {
    if (!isDragging || dragStartX.current === null || dragStartY.current === null) return;

    const now = Date.now();
    if (lastClientX.current !== null && lastMoveTs.current !== null) {
      const dt = now - lastMoveTs.current;
      if (dt > 0) {
        const vx = (clientX - lastClientX.current) / dt;
        // Smooth velocity to avoid noisy spikes while keeping flick detection responsive.
        velocityX.current = velocityX.current * 0.56 + vx * 0.44;
      }
    }
    lastClientX.current = clientX;
    lastClientY.current = clientY;
    lastMoveTs.current = now;

    const delta = clientX - dragStartX.current;
    const deltaY = clientY - dragStartY.current;
    setDragX(delta);
    setDragY(deltaY);
  }

  function maybeSwipeByGesture(clientX: number, clientY: number, pointerType: "touch" | "mouse" | "pen") {
    if (!isDragging || dragStartX.current === null || dragStartY.current === null) {
      resetDrag();
      return;
    }

    const delta = clientX - dragStartX.current;
    const deltaY = clientY - dragStartY.current;
    const isTouch = pointerType === "touch";
    const threshold = isTouch ? SWIPE_THRESHOLD_TOUCH : SWIPE_THRESHOLD_POINTER;
    const flickMinDistance = isTouch ? SWIPE_FLICK_MIN_DISTANCE_TOUCH : SWIPE_FLICK_MIN_DISTANCE_POINTER;
    const flickVelocity = isTouch ? SWIPE_FLICK_VELOCITY_TOUCH : SWIPE_FLICK_VELOCITY_POINTER;
    const absDelta = Math.abs(delta);
    const absVelocity = Math.abs(velocityX.current);
    const shouldSwipe = absDelta >= threshold || (absDelta >= flickMinDistance && absVelocity >= flickVelocity);

    if (shouldSwipe) {
      setIsDragging(false);
      animateSwipe(delta > 0 ? "right" : "left", {
        pointerType,
        velocityX: velocityX.current,
        deltaX: delta,
        deltaY,
      });
      return;
    }

    if (Math.abs(delta) < SWIPE_TAP_THRESHOLD && Math.abs(deltaY) < SWIPE_TAP_THRESHOLD) {
      tryOpenCurrentWebsite();
    }

    resetDrag();
  }

  function handlePointerDown(event: PointerEvent<HTMLElement>) {
    if (isSwipeOutRef.current || swipeOutDirection) return;
    if (event.pointerType === "mouse" && event.button !== 0) return;
    if (shouldIgnoreGestureStart(event.target)) return;
    if (activeGestureInput.current === "touch") return;
    dragPointerId.current = event.pointerId;
    beginDrag(event.clientX, event.clientY, "pointer");
    try {
      event.currentTarget.setPointerCapture(event.pointerId);
    } catch {
      // no-op: some browsers may fail pointer capture on quick taps.
    }
  }

  function handlePointerMove(event: PointerEvent<HTMLElement>) {
    if (isSwipeOutRef.current || swipeOutDirection) return;
    if (dragPointerId.current !== event.pointerId) return;
    if (activeGestureInput.current !== "pointer") return;
    updateDrag(event.clientX, event.clientY);
  }

  function handlePointerUp(event: PointerEvent<HTMLElement>) {
    if (dragPointerId.current !== event.pointerId) {
      resetDrag();
      return;
    }
    dragPointerId.current = null;
    try {
      event.currentTarget.releasePointerCapture(event.pointerId);
    } catch {
      // no-op
    }
    maybeSwipeByGesture(event.clientX, event.clientY, event.pointerType as "touch" | "mouse" | "pen");
  }

  function handleLostPointerCapture(event: PointerEvent<HTMLElement>) {
    if (activeGestureInput.current !== "pointer") return;
    if (dragPointerId.current === null) return;
    if (event.pointerId !== dragPointerId.current) return;

    dragPointerId.current = null;
    const clientX = lastClientX.current ?? dragStartX.current ?? event.clientX;
    const clientY = lastClientY.current ?? dragStartY.current ?? event.clientY;
    maybeSwipeByGesture(clientX, clientY, event.pointerType as "touch" | "mouse" | "pen");
  }

  function findTouchById(event: TouchEvent<HTMLElement>, touchId: number) {
    for (const touch of Array.from(event.changedTouches)) {
      if (touch.identifier === touchId) return touch;
    }
    for (const touch of Array.from(event.touches)) {
      if (touch.identifier === touchId) return touch;
    }
    return null;
  }

  function handleTouchStart(event: TouchEvent<HTMLElement>) {
    if (isSwipeOutRef.current || swipeOutDirection) return;
    if (activeGestureInput.current === "pointer") return;
    if (shouldIgnoreGestureStart(event.target)) return;
    const firstTouch = event.changedTouches[0];
    if (!firstTouch) return;
    dragTouchId.current = firstTouch.identifier;
    beginDrag(firstTouch.clientX, firstTouch.clientY, "touch");
  }

  function handleTouchMove(event: TouchEvent<HTMLElement>) {
    if (isSwipeOutRef.current || swipeOutDirection) return;
    if (activeGestureInput.current !== "touch") return;
    if (dragTouchId.current === null) return;
    const touch = findTouchById(event, dragTouchId.current);
    if (!touch) return;
    updateDrag(touch.clientX, touch.clientY);
  }

  function handleTouchEnd(event: TouchEvent<HTMLElement>) {
    if (activeGestureInput.current !== "touch") {
      resetDrag();
      return;
    }
    if (dragTouchId.current === null) {
      resetDrag();
      return;
    }
    const touch = findTouchById(event, dragTouchId.current);
    const clientX = touch?.clientX ?? (lastClientX.current ?? dragStartX.current ?? 0);
    const clientY = touch?.clientY ?? (lastClientY.current ?? dragStartY.current ?? 0);
    dragTouchId.current = null;
    maybeSwipeByGesture(clientX, clientY, "touch");
  }

  if (!stack.length) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">✨</div>
        <p className="empty-state-text">已经看完这一轮，稍后再来看看新产品吧。</p>
      </div>
    );
  }

  const current = stack[0];
  const nextCard = stack[1] ?? null;
  const backCard = stack[2] ?? null;
  const website = normalizeWebsite(current.website);
  const feedbackDirection = swipeOutDirection || (dragX > SWIPE_FEEDBACK_MIN ? "right" : dragX < -SWIPE_FEEDBACK_MIN ? "left" : null);
  const dragThreshold = gestureInputType === "touch" ? SWIPE_THRESHOLD_TOUCH : SWIPE_THRESHOLD_POINTER;
  const dragProgress = clamp(Math.abs(dragX) / (dragThreshold * 1.45), 0, 1);
  const stackProgress = swipeOutDirection ? 1 : clamp(Math.abs(dragX) / (SWIPE_THRESHOLD_POINTER * 1.04), 0, 1);
  const feedbackOpacity = feedbackDirection ? (swipeOutDirection ? 1 : clamp(Math.abs(dragX) / SWIPE_THRESHOLD_POINTER, 0, 1)) : 0;
  const swipePower = clamp(Math.abs(dragX) / (dragThreshold * 1.08), 0, 1);
  const visualX = dragX;
  const visualY = dragY * 0.08;
  const visualRotate = visualX * 0.047 + dragY * 0.011;
  const fadeOverlayOpacity = feedbackDirection ? (swipeOutDirection ? 1 : dragProgress * 0.92) : 0;
  const activeOpacity = swipeOutDirection ? 0 : clamp(1 - dragProgress * 0.48, 0.22, 1);
  const dragStyle = {
    transform: `translate3d(${visualX}px, ${visualY}px, 0) rotate(${visualRotate}deg)`,
    opacity: activeOpacity,
    transition: isDragging
      ? "none"
      : swipeOutDirection
        ? `transform ${swipeExitMs}ms cubic-bezier(0.2, 0.92, 0.26, 1), opacity ${swipeExitMs}ms ease-out`
        : `transform ${SWIPE_RETURN_MS}ms cubic-bezier(0.2, 0.8, 0.25, 1), opacity ${SWIPE_RETURN_MS}ms ease-out`,
  } as const;

  const nextCardStyle = {
    transform: `translate3d(0, ${16 - stackProgress * 9}px, 0) scale(${0.966 + stackProgress * 0.034})`,
    opacity: 0.58 + stackProgress * 0.3,
  } as const;

  const backCardStyle = {
    transform: `translate3d(0, ${30 - stackProgress * 15}px, 0) scale(${0.938 + stackProgress * 0.052})`,
    opacity: 0.42 + stackProgress * 0.26,
  } as const;
  const hintText =
    feedbackDirection === "right"
      ? "继续右滑，松手即可收藏"
      : feedbackDirection === "left"
        ? "继续左滑，松手跳过"
        : likeStreak >= 2
          ? `连击 x${likeStreak}，继续右滑挖黑马`
          : "左右拖动卡片即可滑动，右滑收藏，左滑跳过";
  const swipeEchoText =
    lastSwipeAction === "right"
      ? lastSwipeHadInertia
        ? "惯性右甩已收藏，继续滑更快"
        : "已收藏，继续右滑快速筛选"
      : lastSwipeHadInertia
        ? "惯性左甩已跳过，继续左滑看下一个"
        : "已跳过，继续左滑看下一个";

  return (
    <div className="discover-shell">
      {showSwipeGuide ? (
        <div className="swipe-onboarding" role="dialog" aria-label="快速发现手势引导">
          <p className="swipe-onboarding__title">左右滑动，30 秒筛出黑马</p>
          <div className="swipe-onboarding__gestures" aria-hidden="true">
            <span className="swipe-onboarding__gesture swipe-onboarding__gesture--left">← 左滑跳过</span>
            <span className="swipe-onboarding__gesture swipe-onboarding__gesture--right">右滑收藏 →</span>
          </div>
          <button className="swipe-onboarding__start" type="button" onClick={dismissSwipeGuide}>
            开始发现
          </button>
        </div>
      ) : null}
      <div className={`swipe-stack ${feedbackDirection ? `is-${feedbackDirection}` : ""}`}>
        {backCard ? (
          <article className="swipe-card swipe-card--ghost swipe-card--ghost-back" style={backCardStyle} aria-hidden="true">
            <header className="swipe-card-header swipe-card-header--ghost">
              <div>
                <h3>{backCard.name}</h3>
                <p>{formatCategories(backCard)}</p>
              </div>
              <span className="swipe-badge">{backCard.dark_horse_index ? `${backCard.dark_horse_index}分` : "精选"}</span>
            </header>
            <p className="swipe-card-desc swipe-card-desc--ghost">{cleanDescription(backCard.description)}</p>
            <div className="swipe-card-meta swipe-card-meta--ghost">
              <span className="swipe-link swipe-link--pending">稍后候选</span>
            </div>
          </article>
        ) : null}

        {nextCard ? (
          <article className="swipe-card swipe-card--ghost swipe-card--ghost-mid" style={nextCardStyle} aria-hidden="true">
            <header className="swipe-card-header swipe-card-header--ghost">
              <div>
                <h3>{nextCard.name}</h3>
                <p>{formatCategories(nextCard)}</p>
              </div>
              <span className="swipe-badge">{nextCard.dark_horse_index ? `${nextCard.dark_horse_index}分` : "精选"}</span>
            </header>
            <p className="swipe-card-desc swipe-card-desc--ghost">{cleanDescription(nextCard.description)}</p>
            <div className="swipe-card-meta swipe-card-meta--ghost">
              <span className="swipe-link swipe-link--pending">下一张候选</span>
            </div>
          </article>
        ) : null}

        <article
          className={`swipe-card is-active ${isDragging ? "is-dragging" : ""} ${feedbackDirection ? `swipe-card--feedback-${feedbackDirection}` : ""}`}
          style={dragStyle}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerCancel={resetDrag}
          onLostPointerCapture={handleLostPointerCapture}
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
          onTouchCancel={resetDrag}
        >
          <div className={`swipe-card__fade ${feedbackDirection ? `is-${feedbackDirection}` : ""}`} style={{ opacity: fadeOverlayOpacity }} aria-hidden="true" />

          <div className={`swipe-feedback ${feedbackDirection ? `is-${feedbackDirection}` : ""}`} style={{ opacity: feedbackOpacity }} aria-hidden="true">
            <span>{feedbackDirection === "right" ? "已收藏" : "已跳过"}</span>
          </div>

          <header className="swipe-card-header">
            <div>
              <h3>{current.name}</h3>
              <p>{formatCategories(current)}</p>
            </div>
            <span className="swipe-badge">{current.dark_horse_index ? `${current.dark_horse_index}分` : "精选"}</span>
          </header>

          <p className="swipe-card-desc">{cleanDescription(current.description)}</p>

          {current.why_matters ? <p className="swipe-card-highlight">💡 {current.why_matters}</p> : null}
          {current.funding_total ? <p className="swipe-card-highlight">💰 {current.funding_total}</p> : null}

          <div className="swipe-card-meta">
            {isValidWebsite(website) ? (
              <a className="swipe-link" href={website} target="_blank" rel="noopener noreferrer">
                了解更多 →
              </a>
            ) : (
              <span className="swipe-link swipe-link--pending">官网待验证</span>
            )}
          </div>
        </article>
      </div>

      <div className="swipe-actions">
        <button className="swipe-btn swipe-btn--nope" type="button" onClick={() => animateSwipe("left")} disabled={!!swipeOutDirection}>
          跳过
        </button>
        <button className="swipe-btn swipe-btn--like" type="button" onClick={() => animateSwipe("right")} disabled={!!swipeOutDirection}>
          收藏
        </button>
      </div>
      <div className={`swipe-echo ${showSwipeEcho ? "is-visible" : ""} ${lastSwipeAction ? `is-${lastSwipeAction}` : ""}`}>
        {swipeEchoText}
      </div>

      <div className="swipe-power" aria-hidden="true">
        <span
          className={`swipe-power__fill ${feedbackDirection ? `is-${feedbackDirection}` : ""}`}
          style={{ transform: `scaleX(${Math.max(0.08, swipePower)})` }}
        />
      </div>
      {likeStreak >= 2 ? <div className={`swipe-streak ${showStreakBurst ? "is-visible" : ""}`}>🔥 黑马连击 x{likeStreak}</div> : null}
      <div className={`swipe-gesture-hint ${feedbackDirection ? `is-${feedbackDirection}` : ""}`}>{hintText}</div>
      <div className="swipe-status">已收藏 {liked} · 已跳过 {skipped}</div>
    </div>
  );
}
