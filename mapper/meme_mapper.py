"""One action per image, portable configuration and character presets."""
import json
from pathlib import Path
from detector.trigger_stabilizer import DEFAULT_SETTINGS
from mapper.presets import ACTION_IDS, BUILTIN_PRESETS, DEFAULT_PRESET

RESERVED_STEMS = frozenset({'default', 'error1', 'error2'})
SUPPORTED_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}


class MemeMapper:
    def __init__(self, meme_dir: Path, config_path: Path):
        self.meme_dir = Path(meme_dir).resolve()
        self.config_path = Path(config_path).resolve()
        self.settings = dict(DEFAULT_SETTINGS)
        self.mappings = {}
        self.enabled = set()
        self.custom_presets = {}
        self.preset_name = DEFAULT_PRESET
        self.imported_images = set()
        self.reload()

    @staticmethod
    def valid_image(path):
        p = Path(path)
        return p.is_file() and p.suffix.lower() in SUPPORTED_EXT and p.stem.lower() not in RESERVED_STEMS

    def _resolve(self, value):
        path = Path(value)
        if not path.is_absolute() and path.parts and path.parts[0] == 'meme':
            return self.meme_dir.joinpath(*path.parts[1:]).resolve()
        return (path if path.is_absolute() else self.config_path.parent / path).resolve()

    def _portable(self, path):
        try:
            return 'meme/' + Path(path).relative_to(self.meme_dir).as_posix()
        except ValueError:
            pass
        try:
            return Path(path).relative_to(self.config_path.parent).as_posix()
        except ValueError:
            return str(path)

    def reload(self):
        self.settings = dict(DEFAULT_SETTINGS)
        self.custom_presets = {}
        self.imported_images = set()
        self.apply_preset(DEFAULT_PRESET)
        if not self.config_path.exists():
            return
        try:
            cfg = json.loads(self.config_path.read_text(encoding='utf-8-sig'))
            self.update_settings(cfg.get('settings', {}))
            self.custom_presets = {name: value for name, value in cfg.get('presets', {}).items()
                                   if name not in BUILTIN_PRESETS and name != 'qq' and isinstance(value, dict)}
            self.imported_images = {self._resolve(p) for p in cfg.get('images', []) if isinstance(p, str)}
            # Older configs are explicit user choices. Keep their valid assignments.
            if cfg.get('version', 1) >= 2:
                self.mappings.clear()
            for trigger, value in cfg.get('mappings', {}).items():
                if trigger in ACTION_IDS and isinstance(value, str):
                    path = self._resolve(value)
                    if self.valid_image(path):
                        self.set_mapping(trigger, path)
            enabled = cfg.get('enabled', list(self.mappings))
            self.enabled = set(enabled) & ACTION_IDS
            self.preset_name = str(cfg.get('preset_name', '사용자 설정'))
            if self.preset_name == 'qq':
                self.preset_name = DEFAULT_PRESET
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            print(f'[MemeMapper] 설정 읽기 실패: {exc}')

    def update_settings(self, settings):
        for key, low, high in [('confirm_ms', 150, 2000), ('hold_ms', 500, 6000), ('neutral_ms', 500, 8000), ('confidence', 0.5, 0.95)]:
            try:
                value = float(settings.get(key, self.settings[key]))
                self.settings[key] = max(low, min(high, value))
            except (TypeError, ValueError):
                pass

    def get_images(self, trigger):
        if trigger not in self.enabled:
            return []
        return [p for p in self.mappings.get(trigger, []) if self.valid_image(p)]

    def get_image(self, trigger):
        images = self.get_images(trigger)
        return images[0] if images else None

    def get_all_triggers(self):
        return {key: list(paths) for key, paths in self.mappings.items()}

    def available_images(self):
        local = set(self.meme_dir.iterdir()) if self.meme_dir.is_dir() else set()
        assigned = {path for paths in self.mappings.values() for path in paths}
        return sorted((p for p in local | assigned | self.imported_images if self.valid_image(p)),
                      key=lambda p: (not p.stem.startswith('pepe_'), p not in assigned, p.name.lower()))

    def import_image(self, path):
        path = Path(path).resolve()
        if not self.valid_image(path):
            raise ValueError('사용 가능한 이미지 파일을 선택하세요.')
        self.imported_images.add(path)

    def assigned_action(self, path):
        path = Path(path).resolve()
        return next((key for key, paths in self.mappings.items() if path in paths), None)

    def assign_image(self, path, trigger):
        path = Path(path).resolve()
        old = self.assigned_action(path)
        if old:
            self.mappings.pop(old)
        if trigger:
            self.set_mapping(trigger, path)
            self.enabled.add(trigger)
        self.preset_name = '사용자 설정'

    def set_mapping(self, trigger, path):
        if trigger not in ACTION_IDS:
            raise ValueError('지원하지 않는 행동입니다.')
        if path is None:
            self.mappings.pop(trigger, None)
            return
        p = Path(path).resolve()
        if not self.valid_image(p):
            raise ValueError('기본·오류 이미지를 제외한 유효한 이미지 파일을 선택하세요.')
        # Enforce a bijection: one image has one action and each action has one image.
        for previous in list(self.mappings):
            if p in self.mappings[previous]:
                self.mappings.pop(previous)
        self.mappings[trigger] = [p]

    def set_enabled(self, trigger, enabled):
        if trigger not in ACTION_IDS:
            return
        if enabled:
            self.enabled.add(trigger)
        else:
            self.enabled.discard(trigger)
        self.preset_name = '사용자 설정'

    def preset_names(self):
        return list(BUILTIN_PRESETS) + sorted(self.custom_presets)

    def apply_preset(self, name):
        preset = BUILTIN_PRESETS.get(name) or self.custom_presets.get(name)
        if preset is None:
            raise ValueError('프리셋을 찾을 수 없습니다.')
        self.mappings.clear()
        for trigger, value in preset.get('mappings', {}).items():
            if trigger not in ACTION_IDS or not isinstance(value, str):
                continue
            path = self.meme_dir / value if name in BUILTIN_PRESETS else self._resolve(value)
            if self.valid_image(path):
                self.set_mapping(trigger, path)
        self.enabled = set(preset.get('enabled', list(self.mappings))) & ACTION_IDS
        self.preset_name = name

    def save_preset(self, name):
        name = name.strip()
        if not name or name in BUILTIN_PRESETS:
            raise ValueError('기본 프리셋과 다른 이름을 입력하세요.')
        self.custom_presets[name] = {'mappings': self._mapping_config(), 'enabled': sorted(self.enabled)}
        self.preset_name = name

    def _mapping_config(self):
        return {key: self._portable(paths[0]) for key, paths in self.mappings.items() if paths}

    def save_config(self):
        cfg = {'version': 2, 'settings': self.settings, 'mappings': self._mapping_config(),
               'enabled': sorted(self.enabled), 'presets': self.custom_presets,
               'preset_name': self.preset_name,
               'images': [self._portable(p) for p in sorted(self.imported_images)]}
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.config_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding='utf-8')
        temporary.replace(self.config_path)
