package com.forzacontroller.app;

import android.app.Activity;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Bundle;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.view.Surface;
import android.view.View;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;

/**
 * Shows the controller page (packed in assets) full screen and feeds it the phone's accelerometer
 * for tilt steering. The page talks to the PC app over ws://PC_ADDRESS:8444/ws.
 */
public class MainActivity extends Activity implements SensorEventListener {
    private WebView web;
    private SensorManager sensors;
    private Sensor accel;
    private Vibrator vibrator;
    private long lastPush = 0;

    @Override
    @SuppressWarnings({"deprecation", "SetJavaScriptEnabled"})
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        web = new WebView(this);
        web.setBackgroundColor(0xFF050A1F);
        web.setOverScrollMode(View.OVER_SCROLL_NEVER);
        setContentView(web);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);   // remembers the PC address and layout
        web.addJavascriptInterface(new Bridge(), "Android");
        web.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest req) {
                return serve(req.getUrl().getPath());
            }
        });
        web.loadUrl("http://app.local/");

        sensors = (SensorManager) getSystemService(SENSOR_SERVICE);
        accel = sensors.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
        vibrator = (Vibrator) getSystemService(VIBRATOR_SERVICE);
        hideSystemUi();
    }

    /** Serves index.html and /static/* from the APK's assets. */
    private WebResourceResponse serve(String path) {
        String name = (path == null || path.equals("/")) ? "index.html"
                : path.startsWith("/static/") ? path.substring(8) : null;
        if (name != null) {
            try {
                InputStream in = getAssets().open(name);
                String mime = name.endsWith(".css") ? "text/css"
                        : name.endsWith(".js") ? "application/javascript" : "text/html";
                return new WebResourceResponse(mime, "utf-8", in);
            } catch (IOException ignored) {
            }
        }
        return new WebResourceResponse("text/plain", "utf-8", 404, "Not found", null,
                new ByteArrayInputStream(new byte[0]));
    }

    @SuppressWarnings("deprecation")
    private void hideSystemUi() {
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                        | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION);
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) hideSystemUi();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (accel != null) sensors.registerListener(this, accel, SensorManager.SENSOR_DELAY_GAME);
        web.onResume();
    }

    @Override
    protected void onPause() {
        sensors.unregisterListener(this);
        web.onPause();
        super.onPause();   // the page releases all buttons when it is hidden
    }

    @Override
    @SuppressWarnings("deprecation")
    public void onSensorChanged(SensorEvent e) {
        long now = System.currentTimeMillis();
        if (now - lastPush < 16) return;   // about 60 updates per second is plenty
        lastPush = now;
        int rot = getWindowManager().getDefaultDisplay().getRotation();
        int angle = rot == Surface.ROTATION_90 ? 90 : rot == Surface.ROTATION_270 ? 270 : 0;
        web.evaluateJavascript("window.onNativeMotion&&onNativeMotion(" + e.values[0] + "," + e.values[1] + "," + angle + ")", null);
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {
    }

    /** Exposed to the page as window.Android. */
    private class Bridge {
        @JavascriptInterface
        public void vibrate(int ms) {
            if (vibrator != null && ms > 0) {
                vibrator.vibrate(VibrationEffect.createOneShot(Math.min(ms, 200), VibrationEffect.DEFAULT_AMPLITUDE));
            }
        }
    }
}
