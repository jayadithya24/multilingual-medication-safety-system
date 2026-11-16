"""Join recorded role views in action order; requires the successful --record run."""
import json
import subprocess
from pathlib import Path
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]


def main():
    result = json.loads((ROOT / 'artifacts/three-role-live-results.json').read_text())
    if not result.get('passed') or not result.get('recorded_video_directory'):
        raise SystemExit('Record a successful three-role run first.')
    directory = Path(result['recorded_video_directory'])
    timeline = json.loads((directory / 'timeline.json').read_text())
    roles = ('patient', 'doctor', 'admin')
    command = [imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner', '-loglevel', 'error', '-y']
    for role in roles:
        command.extend(['-i', str(directory / f'{role}.webm')])
    filters, labels = [], []
    for entry, following in zip(timeline, timeline[1:]):
        if following['seconds'] - entry['seconds'] < .05:
            continue
        number = len(labels)
        label = f'v{number}'
        filters.append(f"[{roles.index(entry['role'])}:v]trim=start={entry['seconds']}:end={following['seconds']},setpts=PTS-STARTPTS,fps=25[{label}]")
        labels.append(f'[{label}]')
    filters.append(''.join(labels) + f'concat=n={len(labels)}:v=1:a=0[out]')
    target = directory / 'three-role-rehearsal.mp4'
    command.extend(['-filter_complex', ';'.join(filters), '-map', '[out]', '-c:v', 'libx264',
                    '-preset', 'fast', '-crf', '23', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(target)])
    subprocess.run(command, check=True)
    print(f'Recorded rehearsal (fictional accounts, no narration): {target}')


if __name__ == '__main__':
    main()
