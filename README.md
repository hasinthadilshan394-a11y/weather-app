# Weather App for Android (Kivy)

This project is a mobile-friendly rewrite of the desktop Tkinter weather app. It uses Kivy and Open-Meteo, so no API key is needed.

## Build an APK online with GitHub Actions

You need a GitHub account. No Android Studio installation is needed on your computer.

1. Download and unzip `weather_apk_project.zip`.
2. Sign in to GitHub and create a **new empty repository** named `weather-app` (a README is optional).
3. Upload the contents of this folder to the repository. Make sure `main.py`, `buildozer.spec`, and `.github/workflows/build-apk.yml` are at the repository root / correct `.github` path. GitHub's **Add file → Upload files** can upload files; create `.github/workflows` first if needed, or use GitHub Desktop.
4. Open the repository's **Actions** tab. If prompted, enable workflows.
5. Select **Build Weather App APK** on the left and click **Run workflow**. A push to `main` also starts a build.
6. Wait for the workflow to finish successfully. Open that run and find **Artifacts** near the bottom.
7. Download `weather-app-debug-apk`, unzip it, and copy the `.apk` to your Android phone.
8. Tap the APK on your phone to install. Android may ask you to allow installs from your browser or file manager. Only install APKs you built or trust.

The first cloud build can take several minutes while Android build tools download. If it fails, open the workflow run and inspect the first red step and its log.

## App features

- City search
- Current temperature, feels-like temperature, humidity, wind speed and conditions
- Five-day high/low forecast
- Favourites for the current app session
- Dark, mobile-friendly Kivy interface

## Notes

- Live data requires internet access.
- The APK from this workflow is a **debug APK** for testing/sideloading, not a Play Store release.
- The app uses Open-Meteo's public geocoding and forecast APIs.
- This workflow uses GitHub Actions and stores the APK as an artifact for 14 days.
