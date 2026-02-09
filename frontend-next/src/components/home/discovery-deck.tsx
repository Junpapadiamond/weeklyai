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
const SWIPE_THRESHOLD_TOUCH = 64;
const SWIPE_THRESHOLD_POINTER = 84;
const SWIPE_OUT_OFFSET = 420;
const SWIPE_EXIT_MS = 240;
const SWIPE_FEEDBACK_MIN = 24;

type DiscoveryDeckProps = {
  products: Product[];
  onLike: (product: Product) => void;
};

type SwipedState = {
  keys: string[];
  timestamp: number;
};

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
  const [isDragging, setIsDragging] = useState(false);
  const [swipeOutDirection, setSwipeOutDirection] = useState<"left" | "right" | null>(null);
  const [lastSwipeAction, setLastSwipeAction] = useState<"left" | "right" | null>(null);
  const [showSwipeEcho, setShowSwipeEcho] = useState(false);
  const dragStartX = useRef<number | null>(null);
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
    dragPointerId.current = null;
    setIsDragging(false);
    if (!isSwipeOutRef.current) {
      setDragX(0);
    }
  }

  function animateSwipe(direction: "left" | "right") {
    if (!stack.length || swipeOutDirection) return;
    const current = stack[0];
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
    setDragX(direction === "right" ? SWIPE_OUT_OFFSET : -SWIPE_OUT_OFFSET);

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
      setSwipeOutDirection(null);
      isSwipeOutRef.current = false;
      dragStartX.current = null;
      dragPointerId.current = null;
      swipeTimerRef.current = null;
    }, SWIPE_EXIT_MS);
  }

  function handlePointerDown(event: PointerEvent<HTMLElement>) {
    if (isSwipeOutRef.current || swipeOutDirection) return;
    if (event.pointerType === "mouse" && event.button !== 0) return;
    dragStartX.current = event.clientX;
    dragPointerId.current = event.pointerId;
    setIsDragging(true);
    setDragX(0);
    try {
      event.currentTarget.setPointerCapture(event.pointerId);
    } catch {
      // no-op: some browsers may fail pointer capture on quick taps.
    }
  }

  function handlePointerMove(event: PointerEvent<HTMLElement>) {
    if (isSwipeOutRef.current || swipeOutDirection) return;
    if (dragPointerId.current !== event.pointerId) return;
    if (!isDragging || dragStartX.current === null) return;
    const delta = event.clientX - dragStartX.current;
    setDragX(delta);
  }

  function handlePointerUp(event: PointerEvent<HTMLElement>) {
    if (dragPointerId.current !== event.pointerId) {
      resetDrag();
      return;
    }
    if (!isDragging || dragStartX.current === null) {
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
  const website = normalizeWebsite(current.website);
  const feedbackDirection = swipeOutDirection || (dragX > SWIPE_FEEDBACK_MIN ? "right" : dragX < -SWIPE_FEEDBACK_MIN ? "left" : null);
  const feedbackOpacity = feedbackDirection ? (swipeOutDirection ? 1 : Math.min(1, Math.abs(dragX) / SWIPE_THRESHOLD_POINTER)) : 0;
  const visualX = swipeOutDirection ? (swipeOutDirection === "right" ? SWIPE_OUT_OFFSET : -SWIPE_OUT_OFFSET) : dragX;
  const dragStyle = {
    transform: `translateX(${visualX}px) rotate(${visualX * 0.04}deg)`,
    opacity: swipeOutDirection ? 0.22 : 1,
    transition: isDragging
      ? "none"
      : swipeOutDirection
        ? `transform ${SWIPE_EXIT_MS}ms cubic-bezier(0.22, 1, 0.36, 1), opacity ${SWIPE_EXIT_MS}ms ease-out`
        : "transform 180ms ease-out, opacity 180ms ease-out",
  } as const;

  return (
    <div className="discover-shell">
      <article
        className={`swipe-card is-active ${isDragging ? "is-dragging" : ""} ${feedbackDirection ? `swipe-card--feedback-${feedbackDirection}` : ""}`}
        style={dragStyle}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={resetDrag}
        onLostPointerCapture={resetDrag}
      >
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
