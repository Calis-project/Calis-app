How the System Understands What Exercise the User Is Doing
To analyze form, your system must first know what exercise is being performed. There are four primary approaches, ranked from simplest to most advanced:

Option A: Heuristics / Rule-Based Detection (Geometric Constrains)
Analyze static structural relationships between coordinates during the first few seconds of a movement:

Horizontal vs. Vertical alignment:
If the vector from Shoulders to Hips is parallel to the ground (angle $\approx 0^\circ$ relative to horizontal), the user is doing a horizontal exercise (e.g., Pushup, Plank, Front Lever).
If the vector is vertical (angle $\approx 90^\circ$ relative to horizontal), it is a vertical exercise (e.g., Squat, Pullup, Handstand, Dip).
Relative joint height checks:
In a Handstand, the ankles are physically higher than the shoulders ($Y_{\text{ankle}} < Y_{\text{shoulder}}$).
In a Pullup, the wrists are higher than the shoulders ($Y_{\text{wrist}} < Y_{\text{shoulder}}$).
In a Squat, the feet are on the floor, and hips move vertically relative to ankles.
Pros: Incredibly lightweight, requires no ML training pipelines, deterministic.
Cons: Fails if the user starts in a strange resting position.
Option B: K-Nearest Neighbors (k-NN) Frame Classifier
Feed MediaPipe coordinate vectors into a simple k-NN classifier:

Compile a small library of labeled frame poses (e.g., 50 frames of pushups-down, 50 frames of squats-down, 50 frames of handstands).
For any incoming frame, normalize the coordinate positions (scale and center them to eliminate camera distance variations).
Find the $K$ closest frames in your database. The majority label wins.
Note: MediaPipe provides a built-in guide for k-NN pose classification on their website.
Pros: Robust to natural variations in body shape, very easy to setup.
Cons: Classifies single frames rather than temporal sequences (e.g., a static pushup posture can look like a plank posture).
Option C: Temporal ML Classifier (LSTMs or 1D CNNs)
Treat the exercise as a sequence of points over time:

Capture time-series chunks of coordinates (e.g., 60 frames / 2 seconds).
Train a small recurrent neural network (LSTM) or 1D Convolutional Neural Network (CNN) on these sequences to predict the class label (e.g., [0: Pushup, 1: Squat, 2: Pullup]).
Pros: Highly accurate, handles transitional movement states flawlessly.
Cons: Requires collection of a labeled dataset of calisthenics videos and training/hosting a custom model.
Option D: Vision-Language Model (VLM) Context Booster (Recommended Startup Strategy)
Use Gemini 1.5 Flash as an orchestrator:

When a user uploads a video or starts a webcam feed, take the first 1-2 seconds of video (or a few keyframes) and send them to the VLM.
Prompt: "Analyze this video. What calisthenics exercise is the user starting to do? Respond with exactly one word from this list: [pushup, pullup, handstand, squat, plank, dip]."
Once Gemini returns the word (e.g., "pushup"), load your specific MediaPipe biomechanics rule engine for pushups.
Pros: 100% robust, requires zero model training, resolves clutter/equipment context (rings vs parallettes vs floor).
Cons: Requires a network API call, but only once per set (not frame-by-frame).