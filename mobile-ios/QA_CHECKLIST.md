# WeeklyAI iOS QA Checklist (v1)

## Functional regression

- Home loads successfully
- Discover swipe deck works (left skip / right save)
- Search returns products and supports navigation
- Product detail renders and related items load
- Blog feed renders and filters switch correctly
- Local favorites add/remove/export works and persists after app restart

## External link behavior

- Product website opens in iOS system Safari
- Blog source link opens in iOS system Safari
- Returning from Safari keeps app state intact

## Network and reliability

- Airplane mode shows network guard and retry button
- Slow network triggers timeout message with retry
- API 429 does not block app rendering
- Recovery from offline to online dismisses error overlay

## UI and safe-area

- iPhone 13/14/15 portrait: header, content, tab bar respect safe area
- Landscape mode: no clipped top/bottom interactive elements
- Favorites panel bottom spacing respects safe area

## Localization

- zh-CN copy displays correctly
- en-US copy displays correctly
- Language preference persists after relaunch

## Pre-submit checks

- App icon and launch screen replaced with release assets
- Bundle ID, version, build number verified
- Privacy URL / Support URL / Content Sources URL reachable
- App Store screenshots match shipped functionality
