"""Shared action vocabulary and built-in character/action presets."""
ACTIONS = [
    ('happy', '웃음', '표정'), ('sad', '슬픔', '표정'),
    ('angry', '화남', '표정'), ('surprised', '놀람', '표정'),
    ('wink', '윙크', '표정'), ('neutral', '대기 / 보통', '표정'),
    ('thumbs_up', '엄지 위', '한 손'), ('thumbs_down', '엄지 아래', '한 손'),
    ('peace', '브이', '한 손'), ('fist', '주먹', '한 손'),
    ('open_palm', '손바닥', '한 손'), ('oneshot', '손바닥 위 + 앞', '한 손'),
    ('ok', 'OK', '한 손'), ('pointing', '검지', '한 손'),
    ('middle_finger', '중지손가락', '한 손'),
    ('rock', '록', '한 손'), ('call_me', '전화해', '한 손'),
    ('three', '세 손가락', '한 손'), ('four', '네 손가락', '한 손'),
    ('gun_finger', '핸드건', '한 손'), ('pinky', '새끼손가락', '한 손'),
    ('heart', '양손 하트', '양손 / 복합'),
    ('handup_fury', '손들고 화남', '양손 / 복합'),
    ('double_gun', '양손 핸드건', '양손 / 복합'),
]
ACTION_IDS = {key for key, _, _ in ACTIONS}
ACTION_LABELS = {key: label for key, label, _ in ACTIONS}
DEFAULT_PRESET = '기본'
DEFAULT_MAPPINGS = {
    'happy': 'pepe_happy.png', 'sad': 'pepe_sad.png', 'angry': 'fury.png',
    'surprised': 'pepe_surprised.png', 'wink': 'eyemiddle.png', 'neutral': 'pepe_neutral.png',
    'thumbs_up': 'thumb.png', 'thumbs_down': 'thumbdown.png',
    'peace': 'double_piece.png', 'fist': 'punch.png', 'open_palm': 'herewego.png',
    'oneshot': 'oneshot.webp', 'pointing': 'forefingerup.gif', 'rock': 'dap.png',
    'call_me': 'shh.png', 'three': 'whynot.png', 'gun_finger': 'fk.webp',
    'handup_fury': 'handup_fury.png',
    'ok': 'smile.png', 'four': 'um.png', 'pinky': 'smoke.png',
    'double_gun': 'verynice.jpg', 'middle_finger': 'fku.png',
}
BUILTIN_PRESETS = {
    DEFAULT_PRESET: {'mappings': DEFAULT_MAPPINGS, 'enabled': list(DEFAULT_MAPPINGS)},
}
