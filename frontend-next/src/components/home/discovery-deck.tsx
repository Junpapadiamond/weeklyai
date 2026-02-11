"use client";

import { PointerEvent, useEffect, useRef, useState } from "react";
import type { Product } from "@/types/api";
import {
  cleanDescription,
  formatCategories,
  isValidWebsite,
  normalizeWebsite,
  productKey,
} from "@/lib/product-utils";

const SWIPED_KEY = "weeklyai_swiped";
const SWIPED_EXPIRY_DAYS = 7;
const SWIPE_THRESHOLD_TOUCH = 70;
const SWIPE_THRESHOLD_POINTER = 92;
const SWIPE_OUT_OFFSET_BASE = 620;
const SWIPE_EXIT_MS = 280;
const SWIPE_RETURN_MS = 220;
const SWIPE_FEEDBACK_MIN = 24;

type DiscoveryDeckProps = {
  products: Product[];
  onLike: (product: Product) => void;
};

type SwipedState = {
  keys: string[];
  timestamp: number;
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
  const [dragX, setDragX] = useState(0);
  const [dragY, setDragY] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [swipeOutDirection, setSwipeOutDirection] = useState<"left" | "right" | null>(null);
  const [lastSwipeAction, setLastSwipeAction] = useState<"left" | "right" | null>(null);
  const [showSwipeEcho, setShowSwipeEcho] = useState(false);
  const dragStartX = useRef<number | null>(null);
  const dragStartY = useRef<number | null>(null);
  const dragPointerId = useRef<number | null>(null);
  const isSwipeOutRef = useRef(false);
  const swipeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const swipeEchoTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const stack = deck.stack;
  const pool = deck.pool;

  useEffect(() => {
    return () => {
      if (swipeTimerRef.current) {
        clearTimeout(swipeTimerRef.current);
      }
      if (swipeEchoTimerRef.current) {
        clearTimeout(swipeEchoTimerRef.current);
      }
      isSwipeOutRef.current = false;
    };
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
    setIsDragging(false);
    if (!isSwipeOutRef.current) {
      setDragX(0);
      setDragY(0);
    }
  }

  function animateSwipe(direction: "left" | "right") {
    if (!stack.length || swipeOutDirection) return;
    const current = stack[0];
    const exitOffset =
      typeof window === "undefined"
        ? SWIPE_OUT_OFFSET_BASE
        : Math.max(SWIPE_OUT_OFFSET_BASE, Math.round(window.innerWidth * 0.92));
    isSwipeOutRef.current = true;
    setSwipeOutDirection(direction);
    setLastSwipeAction(direction);
    setShowSwipeEcho(true);
    if (direction === "right") {
      setLiked((value) => value + 1);
      onLike(current);
    } else {
      setSkipped((value) => value + 1);
    }
    setIsDragging(false);
    setDragX(direction === "right" ? exitOffset : -exitOffset);
    setDragY(dragY * 0.32);

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
      setSwipeOutDirection(null);
      isSwipeOutRef.current = false;
      dragStartX.current = null;
      dragStartY.current = null;
      dragPointerId.current = null;
      swipeTimerRef.current = null;
    }, SWIPE_EXIT_MS);
  }

  function handlePointerDown(event: PointerEvent<HTMLElement>) {
    if (isSwipeOutRef.current || swipeOutDirection) return;
    if (event.pointerType === "mouse" && event.button !== 0) return;
    dragStartX.current = event.clientX;
    dragStartY.current = event.clientY;
    dragPointerId.current = event.pointerId;
    setIsDragging(true);
    setDragX(0);
    setDragY(0);
    try {
      event.currentTarget.setPointerCapture(event.pointerId);
    } catch {
      // no-op: some browsers may fail pointer capture on quick taps.
    }
  }

  function handlePointerMove(event: PointerEvent<HTMLElement>) {
    if (isSwipeOutRef.current || swipeOutDirection) return;
    if (dragPointerId.current !== event.pointerId) return;
    if (!isDragging || dragStartX.current === null || dragStartY.current === null) return;
    const delta = event.clientX - dragStartX.current;
    const deltaY = event.clientY - dragStartY.current;
    setDragX(delta);
    setDragY(deltaY);
  }

  function handlePointerUp(event: PointerEvent<HTMLElement>) {
    if (dragPointerId.current !== event.pointerId) {
      resetDrag();
      return;
    }
    if (!isDragging || dragStartX.current === null || dragStartY.current === null) {
      resetDrag();
      return;
    }

    const delta = event.clientX - dragStartX.current;
    const threshold = event.pointerType === "touch" ? SWIPE_THRESHOLD_TOUCH : SWIPE_THRESHOLD_POINTER;
    if (Math.abs(delta) >= threshold) {
      dragStartX.current = null;
      dragPointerId.current = null;
      setIsDragging(false);
      try {
        event.currentTarget.releasePointerCapture(event.pointerId);
      } catch {
        // no-op
      }
      animateSwipe(delta > 0 ? "right" : "left");
      return;
    }
    try {
      event.currentTarget.releasePointerCapture(event.pointerId);
    } catch {
      // no-op
    }
    resetDrag();
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
  const dragProgress = clamp(Math.abs(dragX) / (SWIPE_THRESHOLD_POINTER * 1.45), 0, 1);
  const stackProgress = swipeOutDirection ? 1 : clamp(Math.abs(dragX) / (SWIPE_THRESHOLD_POINTER * 1.04), 0, 1);
  const feedbackOpacity = feedbackDirection ? (swipeOutDirection ? 1 : clamp(Math.abs(dragX) / SWIPE_THRESHOLD_POINTER, 0, 1)) : 0;
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
        ? `transform ${SWIPE_EXIT_MS}ms cubic-bezier(0.2, 0.92, 0.26, 1), opacity ${SWIPE_EXIT_MS}ms ease-out`
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

  return (
    <div className="discover-shell">
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
          onLostPointerCapture={resetDrag}
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
        {lastSwipeAction === "right" ? "已收藏，继续右滑快速筛选" : "已跳过，继续左滑看下一个"}
      </div>

      <div className="swipe-gesture-hint">左右拖动卡片即可滑动，右滑收藏，左滑跳过</div>
      <div className="swipe-status">已收藏 {liked} · 已跳过 {skipped}</div>
    </div>
  );
}
