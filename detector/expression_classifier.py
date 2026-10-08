"""Map facial movements to actions; scores are movement strengths, not emotion probabilities."""


class ExpressionClassifier:
    @staticmethod
    def classify(face):
        shapes = face.get('blendshapes', {})

        def average(name):
            return (shapes.get(name + 'Left', 0.0) + shapes.get(name + 'Right', 0.0)) / 2

        left_blink = shapes.get('eyeBlinkLeft', 0.0)
        right_blink = shapes.get('eyeBlinkRight', 0.0)
        # Both eyes closing is a blink, not a wink.
        if max(left_blink, right_blink) >= 0.65 and min(left_blink, right_blink) <= 0.25:
            return 'wink', max(left_blink, right_blink)
        scores = {
            'happy': average('mouthSmile'),
            'sad': min(average('mouthFrown'), shapes.get('browInnerUp', 0.0)),
            'angry': min(average('browDown'), max(average('mouthPress'), average('mouthFrown'))),
            # Require upper-face surprise as well as an open mouth to reject normal speech.
            'surprised': min(shapes.get('jawOpen', 0.0),
                             max(average('eyeWide'), shapes.get('browInnerUp', 0.0))),
        }
        action = max(scores, key=scores.get)
        strength = scores[action]
        return (action, strength) if strength >= 0.25 else ('neutral', 1.0 - strength)
