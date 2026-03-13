# WeeklyAI iOS (Capacitor)

This folder contains the iOS App Store shell for WeeklyAI.

## Prerequisites

- Node.js 18+
- Xcode 16+
- CocoaPods

## Setup

```bash
cd mobile-ios
cp .env.example .env
npm install
npm run ios:add
```

## Daily workflow

```bash
cd mobile-ios
source .env
npm run ios:sync
npm run ios:open
```

## Runtime markers

- App shell UA marker: `WeeklyAIApp-iOS/1.0`
- Web app URL: `WEEKLYAI_WEB_URL`
- API host allowlist: derived from `WEEKLYAI_API_URL`

## Release checklist

- Update app icon and launch screen in Xcode asset catalog
- Update bundle identifier, version, and build number
- Confirm external links open in system Safari
- Archive in Xcode and upload to App Store Connect
