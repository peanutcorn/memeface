"""
gesture_classifier.py — 손 랜드마크 → 제스쳐 레이블
MediaPipe Hands 21 랜드마크 기반.

랜드마크 인덱스:
  0: WRIST
  1-4:  THUMB  (CMC, MCP, IP, TIP)
  5-8:  INDEX  (MCP, PIP, DIP, TIP)
  9-12: MIDDLE (MCP, PIP, DIP, TIP)
  13-16: RING  (MCP, PIP, DIP, TIP)
  17-20: PINKY (MCP, PIP, DIP, TIP)

변경 이력
---------
- gun_finger 추가: 엄지 + 검지 (handgun 모양). 방향 무관 거리 기반 검사
- pinky       추가: 새끼손가락만 펴짐
- _ext_dist() 헬퍼: 손목→끝 / 손목→MCP 비율로 방향 무관 펴짐 판정
"""
import math


def _dist(p1, p2) -> float:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def _finger_extended(lm: list, tip: int, pip: int) -> bool:
    """tip.y < pip.y → 손가락 펴짐 (화면 좌표계에서 y 위로 갈수록 작음)"""
    return lm[tip][1] < lm[pip][1]


def _thumb_extended(lm: list, handedness: str) -> bool:
    """엄지는 x축 기준 (좌우 반전 때문에 handedness 고려)"""
    tip = lm[4]
    ip  = lm[3]
    if handedness == 'Right':
        return tip[0] < ip[0]
    else:
        return tip[0] > ip[0]


def _ext_dist(lm: list, tip_idx: int, mcp_idx: int, ratio: float = 1.3) -> bool:
    """방향 무관 손가락 펴짐 판정.
    손목→끝 거리가 손목→MCP 거리의 `ratio` 배 이상이면 펴짐.
    수직/수평/사선 어느 방향이든 동작.
    """
    return _dist(lm[0], lm[tip_idx]) > _dist(lm[0], lm[mcp_idx]) * ratio


def _get_fingers(lm: list, handedness: str) -> list:
    """[엄지, 검지, 중지, 약지, 새끼] 확장 여부 반환 (y축 기반)"""
    return [
        _thumb_extended(lm, handedness),
        _finger_extended(lm, 8,  6),
        _finger_extended(lm, 12, 10),
        _finger_extended(lm, 16, 14),
        _finger_extended(lm, 20, 18),
    ]


def _palm_up_forward(lm: list) -> bool:
    """
    손바닥이 위를 향하고 앞으로 뻗은 자세 감지.

    원리:
    - 손바닥이 위를 향하면 엄지 끝이 검지 관절보다 아래로 내려옴
    - 앞으로 뻗으면 손이 납작하게 (foreshortened) 보임:
      손목→중지끝의 y 거리가 손의 기준 스케일보다 훨씬 짧아짐
    두 조건 AND → 오인식 최소화
    """
    wrist     = lm[0]
    middle_tip = lm[12]
    middle_mcp = lm[9]
    index_mcp  = lm[5]

    hand_scale    = _dist(wrist, middle_mcp)           # 손의 기준 크기
    hand_height_y = abs(middle_tip[1] - wrist[1])      # 손 세로 길이(y축)

    # ① 앞으로 뻗어 납작해 보임
    foreshortened = hand_height_y < hand_scale * 0.7

    # ② 엄지 끝이 검지 관절보다 아래 (손바닥 위 방향)
    thumb_below = lm[4][1] > index_mcp[1]

    return foreshortened and thumb_below


def _is_gun_finger(lm: list) -> bool:
    """
    🔫 handgun 모양: 엄지 + 검지 펴짐, 나머지 접힘.
    방향 무관 거리 기반 판정이므로 손이 옆으로 뻗거나
    엄지가 위로 향한 회전된 자세에서도 동작합니다.
    """
    thumb_ext  = _ext_dist(lm, 4,  2, 1.3)
    index_ext  = _ext_dist(lm, 8,  5, 1.5)
    middle_ext = _ext_dist(lm, 12, 9, 1.3)
    ring_ext   = _ext_dist(lm, 16, 13, 1.3)
    pinky_ext  = _ext_dist(lm, 20, 17, 1.3)

    return (
        thumb_ext and index_ext
        and not middle_ext and not ring_ext and not pinky_ext
    )


def classify_gesture(landmarks: list, handedness: str) -> str | None:
    """
    Args:
        landmarks: list of (x, y, z) tuples (21 points)
        handedness: 'Left' | 'Right'

    Returns:
        gesture label (str) or None
    """
    lm = landmarks
    th, idx, mid, ring, pinky = _get_fingers(lm, handedness)

    hand_scale = _dist(lm[0], lm[9])  # wrist → middle MCP

    # Middle finger only: distances keep this custom pose valid when the hand rotates.
    if hand_scale > 0 and (
        _ext_dist(lm, 12, 9, 1.5)
        and _dist(lm[0], lm[12]) > _dist(lm[0], lm[10]) * 1.2
        and not any(_ext_dist(lm, tip, mcp) for tip, mcp in ((4, 2), (8, 5), (16, 13), (20, 17)))
    ):
        return 'middle_finger'

    # ── 엄지만 펴짐 ─────────────────────────────────────────────────────────
    if th and not idx and not mid and not ring and not pinky:
        tip_y   = lm[4][1]
        wrist_y = lm[0][1]
        mcp_y   = lm[2][1]
        threshold = 0.1 * hand_scale
        if tip_y < wrist_y - threshold:
            return 'thumbs_up'
        if tip_y > mcp_y:
            return 'thumbs_down'

    # ── gun_finger: 엄지 + 검지 (handgun) ───────────────────────────────────
    # 방향 무관 검사 → y축 기반 _get_fingers 결과보다 우선 적용
    if _is_gun_finger(lm):
        return 'gun_finger'

    # ── OK: 엄지 끝 ↔ 검지 끝 가깝고 나머지 펴짐 ───────────────────────────
    if mid and ring and pinky:
        d = _dist(lm[4], lm[8])
        if d < 0.18 * hand_scale:
            return 'ok'

    # ── 검지만 ──────────────────────────────────────────────────────────────
    if not th and idx and not mid and not ring and not pinky:
        return 'pointing'

    # ── 새끼만 (pinky promise) ─────────────────────────────────────────────
    if not th and not idx and not mid and not ring and pinky:
        return 'pinky'

    # ── 검지 + 중지 (평화) ───────────────────────────────────────────────────
    if not th and idx and mid and not ring and not pinky:
        return 'peace'

    # ── 검지 + 새끼 (록) ─────────────────────────────────────────────────────
    if not th and idx and not mid and not ring and pinky:
        return 'rock'

    # ── 엄지 + 새끼 (전화해) ─────────────────────────────────────────────────
    if th and not idx and not mid and not ring and pinky:
        return 'call_me'

    # ── 검지 + 중지 + 약지 ───────────────────────────────────────────────────
    if not th and idx and mid and ring and not pinky:
        return 'three'

    # ── 검지 + 중지 + 약지 + 새끼 ───────────────────────────────────────────
    if not th and idx and mid and ring and pinky:
        return 'four'

    # ── 전부 펴짐: 손바닥 방향으로 oneshot / open_palm 구분 ─────────────────
    if th and idx and mid and ring and pinky:
        if _palm_up_forward(lm):
            return 'oneshot'    # 손바닥 위로 + 앞으로 뻗음
        return 'open_palm'      # 일반 손바닥 (카메라 향함)

    # ── 전부 접힘 ────────────────────────────────────────────────────────────
    if not th and not idx and not mid and not ring and not pinky:
        return 'fist'

    return None


def classify_hand(hand: dict) -> str | None:
    """Prefer model output for basic poses; keep dedicated custom-action rules."""
    custom = classify_gesture(hand['landmarks'], hand['handedness'])
    if custom in {'oneshot', 'ok', 'gun_finger', 'pinky', 'rock', 'call_me', 'three', 'four', 'middle_finger'}:
        return custom
    return hand.get('gesture') or custom


def classify_two_hand_gesture(hand1: dict, hand2: dict, gestures=None) -> str | None:
    """
    양손 제스쳐 감지.
    Args:
        hand1, hand2: {'landmarks': [...], 'handedness': str}
    Returns:
        gesture label or None
    """
    lm1 = hand1['landmarks']
    lm2 = hand2['landmarks']

    # 하트: 양손 call_me + 엄지 끝이 가까움
    g1, g2 = gestures if gestures is not None else (classify_hand(hand1), classify_hand(hand2))
    if g1 == 'call_me' and g2 == 'call_me':
        d = _dist(lm1[4], lm2[4])
        scale = _dist(lm1[0], lm1[9])
        if d < 0.8 * scale:
            return 'heart'

    # 더블 건: 양손 gun_finger
    if g1 == 'gun_finger' and g2 == 'gun_finger':
        return 'double_gun'

    return None
