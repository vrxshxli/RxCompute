## Flutter wrapper
-keep class io.flutter.app.** { *; }
-keep class io.flutter.plugin.** { *; }
-keep class io.flutter.util.** { *; }
-keep class io.flutter.view.** { *; }
-keep class io.flutter.** { *; }
-keep class io.flutter.plugins.** { *; }

## Firebase
-keep class com.google.firebase.** { *; }
-keep class com.google.android.gms.** { *; }

## Google Sign-In
-keep class com.google.android.gms.auth.** { *; }

## Play Core (deferred components) — not used but referenced by Flutter engine
-dontwarn com.google.android.play.core.splitcompat.**
-dontwarn com.google.android.play.core.splitinstall.**
-dontwarn com.google.android.play.core.tasks.**

## Prevent R8 from stripping interface info
-keepattributes *Annotation*
-keepattributes Signature
-keepattributes Exceptions
