import Flutter
import MediaPipeTasksVision
import UIKit

@main
@objc class AppDelegate: FlutterAppDelegate, FlutterImplicitEngineDelegate {
  private let poseQueue = DispatchQueue(label: "calis.pose", qos: .userInitiated)
  private var poseLandmarker: PoseLandmarker?

  override func application(
    _ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
  ) -> Bool {
    return super.application(application, didFinishLaunchingWithOptions: launchOptions)
  }

  func didInitializeImplicitFlutterEngine(_ engineBridge: FlutterImplicitEngineBridge) {
    GeneratedPluginRegistrant.register(with: engineBridge.pluginRegistry)
    let channel = FlutterMethodChannel(
      name: "calis/pose_landmarks",
      binaryMessenger: engineBridge.applicationRegistrar.messenger()
    )
    channel.setMethodCallHandler { [weak self] call, reply in
      guard let self else {
        reply(FlutterError(code: "POSE_ERROR", message: "Bridge unavailable", details: nil))
        return
      }
      guard ["initialize", "detect", "close"].contains(call.method) else {
        reply(FlutterMethodNotImplemented)
        return
      }
      self.poseQueue.async {
        do {
          let value: Any?
          switch call.method {
          case "initialize":
            guard let model = call.arguments as? FlutterStandardTypedData else {
              throw PoseBridgeError.invalidFrame
            }
            try self.initializePose(model.data)
            value = nil
          case "detect":
            guard let frame = call.arguments as? [String: Any] else {
              throw PoseBridgeError.invalidFrame
            }
            value = try self.detectPose(frame)
          default:
            self.poseLandmarker = nil
            value = nil
          }
          DispatchQueue.main.async { reply(value) }
        } catch {
          DispatchQueue.main.async {
            reply(FlutterError(code: "POSE_ERROR", message: error.localizedDescription, details: nil))
          }
        }
      }
    }
  }

  private func initializePose(_ model: Data) throws {
    let path = FileManager.default.temporaryDirectory.appendingPathComponent("calis_pose_landmarker.task")
    try model.write(to: path, options: .atomic)
    let options = PoseLandmarkerOptions()
    options.baseOptions.modelAssetPath = path.path
    options.runningMode = .video
    options.numPoses = 1
    poseLandmarker = try PoseLandmarker(options: options)
  }

  private func detectPose(_ frame: [String: Any]) throws -> [[String: Any]] {
    guard let detector = poseLandmarker,
          let width = frame["width"] as? Int,
          let height = frame["height"] as? Int,
          let rotation = frame["rotation"] as? Int,
          let timestamp = frame["timestampMs"] as? Int,
          let planes = frame["planes"] as? [[String: Any]],
          let plane = planes.first,
          let raw = plane["bytes"] as? FlutterStandardTypedData,
          let bytesPerRow = plane["bytesPerRow"] as? Int,
          width > 0, height > 0, bytesPerRow >= width * 4,
          raw.data.count >= bytesPerRow * height else {
      throw PoseBridgeError.invalidFrame
    }
    guard let provider = CGDataProvider(data: raw.data as CFData),
          let image = CGImage(
            width: width, height: height, bitsPerComponent: 8, bitsPerPixel: 32,
            bytesPerRow: bytesPerRow, space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGBitmapInfo.byteOrder32Little.union(
              CGBitmapInfo(rawValue: CGImageAlphaInfo.premultipliedFirst.rawValue)),
            provider: provider, decode: nil, shouldInterpolate: false,
            intent: .defaultIntent
          ) else {
      throw PoseBridgeError.invalidFrame
    }
    let orientation: UIImage.Orientation
    switch rotation {
    case 90: orientation = .right
    case 180: orientation = .down
    case 270: orientation = .left
    default: orientation = .up
    }
    let input = try MPImage(uiImage: UIImage(cgImage: image, scale: 1, orientation: orientation))
    let detected = try detector.detect(videoFrame: input, timestampInMilliseconds: timestamp)
    return detected.landmarks.first?.map { point in
      [
        "x": point.x,
        "y": point.y,
        "z": point.z,
        "visibility": point.visibility?.floatValue ?? 0,
      ]
    } ?? []
  }
}

private enum PoseBridgeError: Error {
  case invalidFrame
}
