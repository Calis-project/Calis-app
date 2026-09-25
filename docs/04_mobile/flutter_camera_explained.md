# My Flutter Camera Task — Simple Explanation

- **Task / Issue:** #8 / TSK-06 — Flutter Camera Stream & Real-time Preview
- **Purpose:** Explain my small camera implementation in plain English
- **Status:** Foreground camera feature implemented; real-phone performance test pending

---

## 1. What I Built

I built a live camera screen for Calis inside `mobile/`. It shows the back camera's
view and measures how many camera images reach our code each second. The future
exercise-analysis code will need these images. My code does not analyze exercises,
record video, or save images yet.

**Flutter** is the toolkit that builds the app and its screen. **Dart** is the
programming language I use to write it. The **camera package** connects my code
to the phone's camera.

## 2. How My Code Starts

`main()` prepares Flutter, calls `availableCameras()`, and selects the back camera.
**`CameraDescription`** describes a camera, including its name, lens direction,
and sensor orientation; it is not an image. `main()` passes this description into
`CalisApp`, which passes it into `CameraScreen`. If there is no back camera, the
app displays an explanation. It does not switch to the front camera.

A **Widget** describes a part of the interface, such as text or a screen.
`CameraScreen` is a **StatefulWidget** because its associated state, including FPS,
changes while the screen is open. **`initState()`** runs when its state is first
created. That is where I create the **`CameraController`**, choose high resolution, disable audio,
and start initialization.

The controller manages the camera. **`CameraPreview`** displays its live view.
A `Stack` places the FPS label on top of that preview. A small sizing wrapper
fills the screen without stretching the picture, so some edges can be cropped.

## 3. The Preview and the Images Are Different

**`startImageStream()`** asks the package to call my function whenever an image
arrives. Each **`CameraImage`** contains image buffers and information such as its
size and pixel format. It is not a photo file saved to storage.

The preview is what the user sees. The image stream is what our code receives.
A smooth preview does not prove our future analysis code gets 30 images each
second. I count actual image callbacks to measure that separate path.

Later, MediaPipe could receive `image` in this same callback and estimate body
landmarks, such as shoulders and elbows. That future processing will need its
own performance checks. It is not part of my current implementation.

## 4. How I Measure FPS

**FPS** means frames per second:

```text
FPS = frameCount / elapsedSeconds
```

Thirty images in one second means 30 FPS. Thirty images in 1.2 seconds means
25 FPS. I use the actual elapsed time, not an assumption that exactly one second
has passed.

A **`Stopwatch`** measures elapsed time without relying on the wall clock. It
starts after camera initialization. Every callback increments the frame count.
Once at least one second has passed, a callback calculates FPS, updates the label,
logs the result, and starts a new counting window.

The stopwatch keeps running. Only the count and window-start timestamp change.
That lets me compare consecutive frame timestamps correctly across windows.
A gap above 100 ms is logged as a **long frame interval diagnostic**. It suggests
a delay worth checking, but does not prove a dropped frame.

**`setState()`** tells Flutter that the displayed value changed. I use it for the
FPS result about once a second, not on every frame. There is no separate timer
or metrics class. If the stream stops sending images, the old FPS stays visible
until another callback arrives.

## 5. Waiting and Cleaning Up

**`async` / `await`** lets camera setup wait without blocking the entire interface.
For example, I await initialization before starting the image stream.

While waiting, the screen could be removed. **`mounted`** tells me whether its
state still belongs to the widget tree. Checking it prevents starting the stream
or updating the screen after removal.

**`dispose()`** runs when the screen is removed. It stops my stopwatch and starts
camera cleanup. The small cleanup method first stops the image stream, then
releases the controller. Our package version needs that explicit stream stop to
cancel the Dart subscription as well as release native resources.

Startup camera errors are shown as plain text. There is no Retry button or
runtime recovery system. After changing camera permission in Settings, restart
the app.

This version is for a **foreground session**. Putting an app in the background
does not necessarily call the screen's `dispose()`. I have not implemented
background/resume handling, so I must not promise that it recovers automatically.
Restarting the app begins a fresh camera session.

## 6. What Still Needs Testing

The camera feature and emulator functional validation are complete. Static
analysis and all three startup tests passed during the restoration check.
Emulator FPS varied, including startup delays and long frame intervals. The
[engineering report](flutter_camera_report.md) records the observations.
An emulator shares the host computer's resources and uses a virtual camera, so
its FPS neither proves nor disproves the final real-phone requirement.

The three small automated tests check startup error messages. They do not replace
a hardware test of the camera, frame timing, or permissions.

A teammate with a physical Android phone must run the app in profile mode and
check sustained **CameraImage stream FPS**, timing gaps, and preview behavior.
**Stable >=30 FPS and no frame drops are still pending validation.** The picture
looking smooth is not enough evidence.

In a meeting, I can say: “I built a small back-camera preview and real image stream.
I count image callbacks with a stopwatch and display their FPS. The final 30 FPS
performance requirement still needs a physical Android test.”

See the [engineering report](flutter_camera_report.md) for commands, validation
results, and the physical-device checklist.
