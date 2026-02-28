package com.hackfusion.rxcompute

import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import android.content.Context
import io.flutter.embedding.android.FlutterActivity

class MainActivity : FlutterActivity() {
    override fun onStart() {
        super.onStart()
        createNotificationChannel()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val channelId = "rxcompute_alerts"
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val existing = manager.getNotificationChannel(channelId)
        if (existing != null) return

        val channel = NotificationChannel(
            channelId,
            "RxCompute Alerts",
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            description = "Order and refill notifications"
            // Use default system notification sound to avoid missing raw-resource crashes.
            enableVibration(true)
        }
        manager.createNotificationChannel(channel)
    }
}
