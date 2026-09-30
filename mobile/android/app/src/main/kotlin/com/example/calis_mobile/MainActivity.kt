package com.example.calis_mobile

import android.graphics.Bitmap
import android.graphics.Matrix
import android.os.Handler
import android.os.Looper
import com.google.mediapipe.framework.image.BitmapImageBuilder
import com.google.mediapipe.tasks.core.BaseOptions
import com.google.mediapipe.tasks.core.Delegate
import com.google.mediapipe.tasks.vision.core.RunningMode
import com.google.mediapipe.tasks.vision.poselandmarker.PoseLandmarker
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.nio.ByteBuffer
import java.util.concurrent.Executors

class MainActivity : FlutterActivity() {
    private val worker = Executors.newSingleThreadExecutor()
    private val mainHandler = Handler(Looper.getMainLooper())
    private var landmarker: PoseLandmarker? = null
    private var modelBuffer: ByteBuffer? = null
    private var pixelBuffer: IntArray? = null
    private var cachedBitmap: Bitmap? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "calis/pose_landmarks")
            .setMethodCallHandler { call, reply ->
                worker.execute {
                    try {
                        val value: Any? = when (call.method) {
                            "initialize" -> {
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
                                null
                            }
                            "detect" -> detect(call.arguments as Map<*, *>)
                            "close" -> {
                                landmarker?.close()
                                landmarker = null
                                modelBuffer = null
                                cachedBitmap?.recycle()
                                cachedBitmap = null
                                pixelBuffer = null
                                null
                            }
                            else -> {
                                mainHandler.post { reply.notImplemented() }
                                return@execute
                            }
                        }
                        mainHandler.post { reply.success(value) }
                    } catch (error: Exception) {
                        mainHandler.post { reply.error("POSE_ERROR", error.message, null) }
                    }
                }
            }
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
