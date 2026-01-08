# Finance Diagnostics Mobile (Capacitor)

This packages the offline analyzer (demo.html) into a mobile app using Capacitor. A button opens the full web platform (hosted) for registration/payment (Stripe) and dashboard.

## Prerequisites
- Node.js 18+
- Android Studio (for Android)
- Xcode (for iOS, on macOS)

## Setup
```powershell
cd mobile
npm install
# Copy web content into mobile/www
npm run prepare:web
# Initialize native platforms (run once)
npx cap add android
npx cap add ios
# Sync web to native
npx cap sync
```

## Run
- Android: `npm run android`
- iOS: `npm run ios`

## Configure Full Platform URL
Set the hosted URL used for registration/payment and dashboards (Render or other). In the running app (or during development), you can set:
```js
localStorage.setItem('FULL_PLATFORM_URL', 'https://your-app.onrender.com');
```
This is used by the "Open Full Platform" button.

## Notes on Payments
- The mobile app ships the offline analyzer only; the paid features and Stripe Checkout run in the hosted site opened in the system browser (via Capacitor Browser).
- App Store (iOS) policies may require Apple IAP for digital access sold within an iOS app. If you plan App Store distribution, consider routing in-app purchases via Apple IAP and mapping receipts to your backend, or distributing as an enterprise/testing app.

## Rebuild Web Assets
If you change `demo.html`, run:
```powershell
cd mobile
npm run prepare:web
npx cap sync
```

## Troubleshooting
- If CDN libraries (XLSX) aren’t available offline on first run, open the app once while online so assets can cache.
- For deeper offline support, bundle `xlsx.min.js` locally and adjust the script tag in `demo.html`.
