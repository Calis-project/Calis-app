package com.example.calis_mobile

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.Matrix
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.Surface
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.google.mediapipe.framework.image.BitmapImageBuilder
import com.google.mediapipe.tasks.core.BaseOptions
import com.google.mediapipe.tasks.core.Delegate
import com.google.mediapipe.tasks.vision.core.ImageProcessingOptions
import com.google.mediapipe.tasks.vision.core.RunningMode
import com.google.mediapipe.tasks.vision.poselandmarker.PoseLandmarker
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.EventChannel
import io.flutter.plugin.common.MethodChannel
import io.flutter.view.TextureRegistry
import java.nio.ByteBuffer
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean

class MainActivity : FlutterActivity() {
    companion object {
        private const val CAMERA_PERMISSION_REQUEST_CODE = 1001
    }

    private val worker = Executors.newSingleThreadExecutor()
    private val cameraAnalysisExecutor = Executors.newSingleThreadExecutor()
    private val mainHandler = Handler(Looper.getMainLooper())
    private var landmarker: PoseLandmarker? = null
    private var modelBuffer: ByteBuffer? = null
    private var pixelBuffer: IntArray? = null
    private var cachedBitmap: Bitmap? = null

    // Native CameraX & Stream
    private var cameraProvider: ProcessCameraProvider? = null
    private var surfaceTextureEntry: TextureRegistry.SurfaceTextureEntry? = null
    private var eventSink: EventChannel.EventSink? = null
    private var lastNativeTimestampMs = -1L
    private val isAnalyzing = AtomicBoolean(false)
    private var totalCameraFrames = 0
    private var pendingCameraReply: MethodChannel.Result? = null
    private var pendingCameraEngine: FlutterEngine? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        EventChannel(flutterEngine.dartExecutor.binaryMessenger, "calis/pose_landmarks_stream")
            .setStreamHandler(object : EventChannel.StreamHandler {
                override fun onListen(arguments: Any?, events: EventChannel.EventSink?) {
                    eventSink = events
                }

                override fun onCancel(arguments: Any?) {
                    eventSink = null
                }
            })

        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "calis/pose_landmarks")
            .setMethodCallHandler { call, reply ->
                when (call.method) {
                    "initialize" -> {
                        worker.execute {
                            try {
                                landmarker?.close()
                                val modelBytes = call.arguments as ByteArray
                                modelBuffer = ByteBuffer.allocateDirect(modelBytes.size).apply {
                                    put(modelBytes)
                                    rewind()
                                }
                                val optionsBuilder = { delegate: Delegate ->
                                    val base = BaseOptions.builder()
                                        .setModelAssetBuffer(modelBuffer!!)
                                        .setDelegate(delegate)
                                        .build()
                                    PoseLandmarker.PoseLandmarkerOptions.builder()
                                        .setBaseOptions(base)
                                        .setRunningMode(RunningMode.VIDEO)
                                        .setNumPoses(1)
                                        .build()
                                }
                                landmarker = try {
                                    PoseLandmarker.createFromOptions(this, optionsBuilder(Delegate.GPU))
                                } catch (gpuError: Exception) {
                                    PoseLandmarker.createFromOptions(this, optionsBuilder(Delegate.CPU))
                                }
                                mainHandler.post { reply.success(null) }
                            } catch (error: Exception) {
                                mainHandler.post { reply.error("INIT_ERROR", error.message, null) }
                            }
                        }
                    }
                    "startNativeCamera" -> {
                        startNativeCamera(flutterEngine, reply)
                    }
                    "stopNativeCamera" -> {
                        stopNativeCamera()
                        reply.success(null)
                    }
                    "detect" -> {
                        worker.execute {
                            try {
                                val value = detect(call.arguments as Map<*, *>)
                                mainHandler.post { reply.success(value) }
                            } catch (error: Exception) {
                                mainHandler.post { reply.error("POSE_ERROR", error.message, null) }
                            }
                        }
                    }
                    "close" -> {
                        worker.execute {
                            stopNativeCamera()
                            landmarker?.close()
                            landmarker = null
                            modelBuffer = null
                            cachedBitmap?.recycle()
                            cachedBitmap = null
                            pixelBuffer = null
                            mainHandler.post { reply.success(null) }
                        }
                    }
                    else -> reply.notImplemented()
                }
            }
    }

    private fun startNativeCamera(flutterEngine: FlutterEngine, reply: MethodChannel.Result) {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            pendingCameraReply = reply
            pendingCameraEngine = flutterEngine
            ActivityCompat.requestPermissions(
                this,
                arrayOf(Manifest.permission.CAMERA),
                CAMERA_PERMISSION_REQUEST_CODE
            )
            return
        }
        bindNativeCamera(flutterEngine, reply)
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == CAMERA_PERMISSION_REQUEST_CODE) {
            val reply = pendingCameraReply
            val engine = pendingCameraEngine
            pendingCameraReply = null
            pendingCameraEngine = null
            if (reply != null) {
                if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                    if (engine != null) {
                        bindNativeCamera(engine, reply)
                    } else {
                        reply.error("CAMERA_ERROR", "Flutter engine unavailable after permission grant", null)
                    }
                } else {
                    reply.error("PERMISSION_DENIED", "Camera permission is required to start camera", null)
                }
            }
        }
    }

    private fun bindNativeCamera(flutterEngine: FlutterEngine, reply: MethodChannel.Result) {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(this)
        cameraProviderFuture.addListener({
            try {
                cameraProvider = cameraProviderFuture.get()
                cameraProvider?.unbindAll()

                surfaceTextureEntry?.release()
                val entry = flutterEngine.renderer.createSurfaceTexture()
                surfaceTextureEntry = entry

                var replyDispatched = false

                val preview = Preview.Builder().build()
                preview.setSurfaceProvider(ContextCompat.getMainExecutor(this)) { request ->
                    val surfaceTexture = entry.surfaceTexture()
                    val negotiatedWidth = request.resolution.width
                    val negotiatedHeight = request.resolution.height
                    surfaceTexture.setDefaultBufferSize(negotiatedWidth, negotiatedHeight)
                    val surface = Surface(surfaceTexture)
                    request.provideSurface(surface, ContextCompat.getMainExecutor(this)) {
                        surface.release()
                    }

                    if (!replyDispatched) {
                        replyDispatched = true
                        reply.success(
                            mapOf(
                                "textureId" to entry.id(),
                                "width" to negotiatedWidth,
                                "height" to negotiatedHeight
                            )
                        )
                    }
                }

                val imageAnalysis = ImageAnalysis.Builder()
                    .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                    .setOutputImageFormat(ImageAnalysis.OUTPUT_IMAGE_FORMAT_RGBA_8888)
                    .build()

                imageAnalysis.setAnalyzer(cameraAnalysisExecutor) { imageProxy ->
                    totalCameraFrames++
                    val currentCameraFrames = totalCameraFrames

                    if (isAnalyzing.compareAndSet(false, true)) {
                        try {
                            val detector = landmarker
                            if (detector != null) {
                                val timestampMs = imageProxy.imageInfo.timestamp / 1_000_000
                                val monotonicTimestamp = if (timestampMs > lastNativeTimestampMs) timestampMs else lastNativeTimestampMs + 1
                                lastNativeTimestampMs = monotonicTimestamp
                                val rotationDegrees = imageProxy.imageInfo.rotationDegrees
                                val frameWidth = imageProxy.width
                                val frameHeight = imageProxy.height

                                val bitmap = imageProxy.toBitmap()
                                imageProxy.close()

                                worker.execute {
                                    try {
                                        val mpImage = BitmapImageBuilder(bitmap).build()
                                        val options = ImageProcessingOptions.builder()
                                            .setRotationDegrees(rotationDegrees)
                                            .build()

                                        val t0 = System.currentTimeMillis()
                                        val result = detector.detectForVideo(mpImage, options, monotonicTimestamp)
                                        val elapsed = System.currentTimeMillis() - t0

                                        val rawList = result.landmarks().firstOrNull()?.map { point ->
                                            mapOf(
                                                "x" to point.x(),
                                                "y" to point.y(),
                                                "z" to point.z(),
                                                "visibility" to point.visibility().orElse(0f)
                                            )
                                        } ?: emptyList()

                                        mainHandler.post {
                                            eventSink?.success(
                                                mapOf(
                                                    "landmarks" to rawList,
                                                    "latencyMs" to elapsed,
                                                    "width" to frameWidth,
                                                    "height" to frameHeight,
                                                    "rotation" to rotationDegrees,
                                                    "cameraFrameCount" to currentCameraFrames
                                                )
                                            )
                                        }
                                    } catch (e: Exception) {
                                        Log.e("CalisPose", "Worker inference error", e)
                                    } finally {
                                        bitmap.recycle()
                                        isAnalyzing.set(false)
                                    }
                                }
                            } else {
                                imageProxy.close()
                                isAnalyzing.set(false)
                            }
                        } catch (e: Exception) {
                            Log.e("CalisPose", "Analyzer extraction error", e)
                            imageProxy.close()
                            isAnalyzing.set(false)
                        }
                    } else {
                        // Drop frame immediately so CameraX pipeline does not block
                        imageProxy.close()
                    }
                }

                val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA
                cameraProvider?.bindToLifecycle(this, cameraSelector, preview, imageAnalysis)
            } catch (e: Exception) {
                Log.e("CalisPose", "startNativeCamera failed", e)
                reply.error("CAMERA_START_FAILED", e.message, null)
            }
        }, ContextCompat.getMainExecutor(this))
    }

    private fun stopNativeCamera() {
        mainHandler.post {
            cameraProvider?.unbindAll()
            cameraProvider = null
            surfaceTextureEntry?.release()
            surfaceTextureEntry = null
        }
        totalCameraFrames = 0
        isAnalyzing.set(false)
    }

    private fun detect(frame: Map<*, *>): List<Map<String, Float>> {
        val detector = checkNotNull(landmarker) { "MediaPipe is not initialized" }
        val width = frame["width"] as Int
        val height = frame["height"] as Int
        val rotation = frame["rotation"] as Int
        val timestamp = (frame["timestampMs"] as Number).toLong()
        val planes = frame["planes"] as List<*>
        val y = planes[0] as Map<*, *>
        val u = planes[1] as Map<*, *>
        val v = planes[2] as Map<*, *>
        val yBytes = y["bytes"] as ByteArray
        val uBytes = u["bytes"] as ByteArray
        val vBytes = v["bytes"] as ByteArray
        val yStride = y["bytesPerRow"] as Int
        val uStride = u["bytesPerRow"] as Int
        val vStride = v["bytesPerRow"] as Int
        val yPixelStride = y["bytesPerPixel"] as Int
        val uPixelStride = u["bytesPerPixel"] as Int
        val vPixelStride = v["bytesPerPixel"] as Int

        val targetWidth = if (rotation == 90 || rotation == 270) height else width
        val targetHeight = if (rotation == 90 || rotation == 270) width else height

        if (pixelBuffer == null || pixelBuffer!!.size < width * height) {
            pixelBuffer = IntArray(width * height)
        }
        val pixels = pixelBuffer!!

        when (rotation) {
            90 -> {
                for (row in 0 until height) {
                    val chromaRow = row shr 1
                    val uRowOffset = chromaRow * uStride
                    val vRowOffset = chromaRow * vStride
                    val yRowOffset = row * yStride
                    val outCol = height - 1 - row
                    for (col in 0 until width) {
                        val chromaCol = col shr 1
                        val cb = (uBytes[uRowOffset + chromaCol * uPixelStride].toInt() and 0xff) - 128
                        val cr = (vBytes[vRowOffset + chromaCol * vPixelStride].toInt() and 0xff) - 128
                        val luma = yBytes[yRowOffset + col * yPixelStride].toInt() and 0xff
                        val r = (luma + ((1436 * cr) shr 10)).coerceIn(0, 255)
                        val g = (luma - ((352 * cb + 731 * cr) shr 10)).coerceIn(0, 255)
                        val b = (luma + ((1815 * cb) shr 10)).coerceIn(0, 255)
                        pixels[col * targetWidth + outCol] = (0xff shl 24) or (r shl 16) or (g shl 8) or b
                    }
                }
            }
            270 -> {
                for (row in 0 until height) {
                    val chromaRow = row shr 1
                    val uRowOffset = chromaRow * uStride
                    val vRowOffset = chromaRow * vStride
                    val yRowOffset = row * yStride
                    val outCol = row
                    for (col in 0 until width) {
                        val chromaCol = col shr 1
                        val cb = (uBytes[uRowOffset + chromaCol * uPixelStride].toInt() and 0xff) - 128
                        val cr = (vBytes[vRowOffset + chromaCol * vPixelStride].toInt() and 0xff) - 128
                        val luma = yBytes[yRowOffset + col * yPixelStride].toInt() and 0xff
                        val r = (luma + ((1436 * cr) shr 10)).coerceIn(0, 255)
                        val g = (luma - ((352 * cb + 731 * cr) shr 10)).coerceIn(0, 255)
                        val b = (luma + ((1815 * cb) shr 10)).coerceIn(0, 255)
                        val outRow = width - 1 - col
                        pixels[outRow * targetWidth + outCol] = (0xff shl 24) or (r shl 16) or (g shl 8) or b
                    }
                }
            }
            180 -> {
                for (row in 0 until height) {
                    val chromaRow = row shr 1
                    val uRowOffset = chromaRow * uStride
                    val vRowOffset = chromaRow * vStride
                    val yRowOffset = row * yStride
                    val outRow = height - 1 - row
                    val outRowOffset = outRow * targetWidth
                    for (col in 0 until width) {
                        val chromaCol = col shr 1
                        val cb = (uBytes[uRowOffset + chromaCol * uPixelStride].toInt() and 0xff) - 128
                        val cr = (vBytes[vRowOffset + chromaCol * vPixelStride].toInt() and 0xff) - 128
                        val luma = yBytes[yRowOffset + col * yPixelStride].toInt() and 0xff
                        val r = (luma + ((1436 * cr) shr 10)).coerceIn(0, 255)
                        val g = (luma - ((352 * cb + 731 * cr) shr 10)).coerceIn(0, 255)
                        val b = (luma + ((1815 * cb) shr 10)).coerceIn(0, 255)
                        val outCol = width - 1 - col
                        pixels[outRowOffset + outCol] = (0xff shl 24) or (r shl 16) or (g shl 8) or b
                    }
                }
            }
            else -> {
                for (row in 0 until height) {
                    val chromaRow = row shr 1
                    val uRowOffset = chromaRow * uStride
                    val vRowOffset = chromaRow * vStride
                    val yRowOffset = row * yStride
                    val outRowOffset = row * targetWidth
                    for (col in 0 until width) {
                        val chromaCol = col shr 1
                        val cb = (uBytes[uRowOffset + chromaCol * uPixelStride].toInt() and 0xff) - 128
                        val cr = (vBytes[vRowOffset + chromaCol * vPixelStride].toInt() and 0xff) - 128
                        val luma = yBytes[yRowOffset + col * yPixelStride].toInt() and 0xff
                        val r = (luma + ((1436 * cr) shr 10)).coerceIn(0, 255)
                        val g = (luma - ((352 * cb + 731 * cr) shr 10)).coerceIn(0, 255)
                        val b = (luma + ((1815 * cb) shr 10)).coerceIn(0, 255)
                        pixels[outRowOffset + col] = (0xff shl 24) or (r shl 16) or (g shl 8) or b
                    }
                }
            }
        }

        if (cachedBitmap == null || cachedBitmap!!.width != targetWidth || cachedBitmap!!.height != targetHeight) {
            cachedBitmap?.recycle()
            cachedBitmap = Bitmap.createBitmap(targetWidth, targetHeight, Bitmap.Config.ARGB_8888)
        }
        val bitmap = cachedBitmap!!
        bitmap.setPixels(pixels, 0, targetWidth, 0, 0, targetWidth, targetHeight)

        val result = detector.detectForVideo(BitmapImageBuilder(bitmap).build(), timestamp)
        return result.landmarks().firstOrNull()?.map { point ->
            mapOf(
                "x" to point.x(),
                "y" to point.y(),
                "z" to point.z(),
                "visibility" to point.visibility().orElse(0f),
            )
        } ?: emptyList()
    }

    override fun onDestroy() {
        worker.execute {
            stopNativeCamera()
            landmarker?.close()
            landmarker = null
            modelBuffer = null
            cachedBitmap?.recycle()
            cachedBitmap = null
            pixelBuffer = null
        }
        worker.shutdown()
        super.onDestroy()
    }
}
