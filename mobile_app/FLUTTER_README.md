# Flutter Mobile App for Quran Center

This directory contains the complete source code for the Android application built with Flutter. It is designed to be **Offline-First**, meaning it works fully without an internet connection and syncs data when online.

## Architecture

- **Framework:** Flutter (Dart)
- **State Management:** Riverpod
- **Local Database:** Drift (SQLite)
- **Network:** Dio
- **Architecture:** MVVM (Model-View-ViewModel)

## Prerequisites

1.  **Flutter SDK:** Install from [flutter.dev](https://flutter.dev/docs/get-started/install).
2.  **Android Studio / VS Code:** With Flutter plugins installed.
3.  **Flask Backend:** Must be running (see root `README.md`).

## Setup Instructions

1.  **Navigate to the mobile app directory:**
    ```bash
    cd mobile_app
    ```

2.  **Install Dependencies:**
    ```bash
    flutter pub get
    ```

3.  **Generate Database Code:**
    This project uses `drift` which requires code generation. Run:
    ```bash
    dart run build_runner build
    ```
    *If you modify the database schema in `lib/data/database/database.dart`, run this command again.*

4.  **Configure API URL:**
    Open `lib/services/api_service.dart`.
    - If running on **Android Emulator**, use `http://10.0.2.2:5000/api`.
    - If running on a **Physical Device**, use your computer's IP address (e.g., `http://192.168.1.50:5000/api`).

5.  **Build & Run:**
    - Connect your device or start emulator.
    - Run:
      ```bash
      flutter run
      ```

6.  **Build APK for Release:**
    ```bash
    flutter build apk --release
    ```
    The APK will be located at `build/app/outputs/flutter-apk/app-release.apk`.

## Features

- **Offline Support:** All data (students, reports, circles) is stored locally in SQLite.
- **Sync Mechanism:**
    - **Pull:** Downloads latest data from server on login and refresh.
    - **Push:** Uploads offline actions (new reports) when internet is available.
- **Role Support:** Adapts data based on logged-in user (Teacher/Admin).
- **RTL Support:** Full Arabic interface.

## Project Structure

- `lib/data/database`: Local database schema and access objects.
- `lib/providers`: State management logic (Auth, Sync).
- `lib/services`: External communication (API, Sync Logic).
- `lib/ui/screens`: Application pages.
- `lib/ui/widgets`: Reusable UI components.

## Troubleshooting

- **Connection Refused:** Ensure Flask is running and the IP address in `api_service.dart` is correct.
- **Database Errors:** Run `dart run build_runner build --delete-conflicting-outputs` to regenerate schema code.
