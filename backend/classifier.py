import math


class GestureClassifier:
    """
    Classifies a hand gesture from 21 MediaPipe hand landmarks.

    Landmark reference:
      Wrist = 0
      Thumb:  CMC=1, MCP=2, IP=3, TIP=4
      Index:  MCP=5, PIP=6, DIP=7, TIP=8
      Middle: MCP=9, PIP=10, DIP=11, TIP=12
      Ring:   MCP=13, PIP=14, DIP=15, TIP=16
      Pinky:  MCP=17, PIP=18, DIP=19, TIP=20

    All distance thresholds are normalized by the hand's own size (wrist to
    middle-finger MCP), so classification stays accurate whether the hand is
    close to or far from the camera. Thumb direction uses the detected
    handedness so it works correctly for both left and right hands.
    """

    # Tunable, but sensible defaults
    PINCH_THRESHOLD = 0.18          # pinch_dist / hand_scale
    THUMB_VERTICAL_THRESHOLD = 0.55  # thumb_tip vertical offset / hand_scale

    def __init__(self):
        pass

    @staticmethod
    def _dist(a, b):
        return math.hypot(a.x - b.x, a.y - b.y)

    def _hand_scale(self, lm):
        """Reference size of the hand in the frame, used to normalize thresholds."""
        scale = self._dist(lm[0], lm[9])
        return scale if scale > 1e-6 else 1e-6

    def _fingers_up(self, lm, handedness_label):
        """
        Returns [thumb, index, middle, ring, pinky] booleans for whether each
        finger is extended, robust to hand rotation by comparing distance
        from the wrist rather than raw y-coordinates alone where possible.
        """
        wrist = lm[0]

        # Index -> Pinky: a finger is "up" if its tip is farther from the
        # wrist than its PIP joint is, along the hand's own vertical axis.
        index_up = lm[8].y < lm[6].y
        middle_up = lm[12].y < lm[10].y
        ring_up = lm[16].y < lm[14].y
        pinky_up = lm[20].y < lm[18].y

        # Thumb: extended sideways relative to the palm. Compare x position
        # of tip vs the IP joint, using handedness so it's correct for both
        # hands regardless of mirroring.
        if handedness_label == "Right":
            thumb_extended = lm[4].x < lm[3].x
        else:
            thumb_extended = lm[4].x > lm[3].x

        return [thumb_extended, index_up, middle_up, ring_up, pinky_up]

    def classify(self, hand_landmarks, handedness_label="Right"):
        """
        Classifies hand gesture based on 21 MediaPipe landmarks.
        `handedness_label` should be "Left" or "Right" as reported by MediaPipe.
        Returns gesture name string.
        """
        lm = hand_landmarks.landmark
        scale = self._hand_scale(lm)

        thumb_ext, index_up, middle_up, ring_up, pinky_up = self._fingers_up(
            lm, handedness_label
        )

        four_fingers = index_up and middle_up and ring_up and pinky_up
        four_curled = not index_up and not middle_up and not ring_up and not pinky_up

        # --- Open Palm (all 4 fingers up) ---
        if four_fingers:
            return "Open Palm"

        # --- Thumb-only gestures: index/middle/ring/pinky all curled ---
        # Checked before Pinch so a compact fist (where the thumb can rest
        # close to the curled fingers) is never misread as a pinch.
        if four_curled:
            # How far above/below the wrist the thumb tip sits, normalized.
            # Positive = thumb points up, negative = thumb points down.
            thumb_vertical = (lm[0].y - lm[4].y) / scale

            if thumb_ext and thumb_vertical > self.THUMB_VERTICAL_THRESHOLD:
                return "Thumbs Up"
            if thumb_vertical < -self.THUMB_VERTICAL_THRESHOLD:
                return "Thumbs Down"

            return "Closed Fist"

        # --- Pinch (thumb tip close to index tip), normalized by hand size ---
        pinch_dist = self._dist(lm[4], lm[8]) / scale
        if pinch_dist < self.PINCH_THRESHOLD:
            return "Pinch"

        # --- Pointing Finger (only index up) ---
        if index_up and not middle_up and not ring_up and not pinky_up:
            return "Pointing Finger"

        # --- Victory / Peace (index + middle up) ---
        if index_up and middle_up and not ring_up and not pinky_up:
            return "Victory Sign"

        # --- Three Fingers (index + middle + ring) ---
        if index_up and middle_up and ring_up and not pinky_up:
            return "Three Fingers"

        # --- Rock Sign (index + pinky up, middle + ring down) ---
        if index_up and not middle_up and not ring_up and pinky_up:
            return "Rock Sign"

        return "Unknown"
