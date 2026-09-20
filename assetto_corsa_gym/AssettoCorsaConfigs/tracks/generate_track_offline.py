"""
Офлайн-аналог generate_track.ipynb: строит track_file/ref_lap_file/track_grid_file
без живого AC (без сокета get_track_info/get_static_info).

Обоснование: geometry, которую отдаёт live-путь (client.export_track_and_racing_line,
ac_client.py:184-231), целиком вычисляется StaticInfo/Track внутри плагина
(structures.py:258-329) из одного статического файла игры:
  content/tracks/<track>[/<config>]/ai/fast_lane.ai
Живой сокет здесь не источник данных, а транспорт: тот же файл, тот же расчёт.
Единственное поле, которого нет в файле, - TrackLength из ac.getTrackLength() -
но ac_env.py:638 всё равно перезаписывает config.yaml-значение live-данными
при первом reset(), так что офлайн-приближение (последний dist в fast_lane.ai)
безопасно как заглушка.

Логика parse_fast_lane порт-в-порт со structures.py:281-321 (Track.__init__).
Логика occupancy grid - те же вызовы, что в generate_track.ipynb (cells 15-31):
AssettoCorsaEnv.track.Track + AssettoCorsaEnv.track.in_quadrilateral.

Использование:
    python generate_track_offline.py \
        --ac-content "X:\\SteamLibrarySSD\\steamapps\\common\\assettocorsa" \
        --track magione
"""
import argparse
import math
import os
import pickle
import struct
import sys
from operator import itemgetter

import numpy as np
import pandas as pd


def parse_fast_lane(fast_lane_path):
    """Порт structures.py:281-321 (без throttle/brake/speed/angle - не нужны экспорту)."""
    with open(fast_lane_path, "rb") as buffer:
        _header, detail_count, _u1, _u2 = struct.unpack("4i", buffer.read(4 * 4))

        data_ideal = []
        for _ in range(detail_count):
            data_ideal.append(struct.unpack("4f i", buffer.read(4 * 5)))

        data_detail = []
        for _ in range(detail_count):
            data_detail.append(struct.unpack("18f", buffer.read(4 * 18)))

    left_array = []
    right_array = []
    for i in range(detail_count):
        x, _y, z, _dist, _idx = data_ideal[i]
        right, left = itemgetter(6, 7)(data_detail[i])

        index_n = i - 1 if i > 0 else detail_count - 1
        angle = math.degrees(math.atan2(data_ideal[index_n][2] - z, x - data_ideal[index_n][0])) * -1

        lx = x + math.cos((-angle - 90) * math.pi / 180) * left
        lz = z - math.sin((-angle - 90) * math.pi / 180) * left
        rx = x + math.cos((-angle + 90) * math.pi / 180) * right
        rz = z - math.sin((-angle + 90) * math.pi / 180) * right

        # Именование left_array/right_array как в оригинале (structures.py:311-312) -
        # де-факто стороны переставлены местами, но для occupancy grid это не важно
        # (track.py:88-94 строит quad из пар точек безотносительно семантики стороны).
        left_array.append((rz, rx))
        right_array.append((lz, lx))

    fast_lane = [(el[2], el[0]) for el in data_ideal]
    track_length = data_ideal[-1][3]
    return left_array, right_array, fast_lane, track_length


def resolve_track_dir(ac_content_path, track_name, track_configuration):
    """Порт логики ac_client.py TrackFullName + structures.py:269-271 (fileDest)."""
    track_dir = os.path.join(ac_content_path, "content", "tracks", track_name)
    if track_configuration:
        candidate = os.path.join(track_dir, track_configuration)
        if os.path.isdir(candidate):
            track_dir = candidate
    return track_dir


def export_track_and_racing_line(ac_content_path, track_name, track_configuration, output_path):
    """Порт ac_client.py:184-231, данные - через parse_fast_lane вместо сокета."""
    track_dir = resolve_track_dir(ac_content_path, track_name, track_configuration)
    fast_lane_path = os.path.join(track_dir, "ai", "fast_lane.ai")
    if not os.path.isfile(fast_lane_path):
        raise FileNotFoundError(f"Не найден {fast_lane_path}")

    left_array, right_array, fast_lane, track_length = parse_fast_lane(fast_lane_path)

    track_full_name = track_name if not track_configuration else f"{track_name}-{track_configuration}"

    left_border = np.array(left_array)
    right_border = np.array(right_array)
    fast_lane_arr = np.array(fast_lane)

    os.makedirs(output_path, exist_ok=True)

    track_file = os.path.join(output_path, f"{track_full_name}.csv")
    pd.DataFrame({
        "left_border_x": left_border[:, 0],
        "left_border_y": left_border[:, 1],
        "right_border_x": right_border[:, 0],
        "right_border_y": right_border[:, 1],
        "pos_x": fast_lane_arr[:, 0],
        "pos_y": fast_lane_arr[:, 1],
    }).to_csv(track_file, index=False)

    ref_line_file = os.path.join(output_path, f"{track_full_name}-racing_line.csv")
    pd.DataFrame({
        "pos_x": fast_lane_arr[:, 0],
        "pos_y": fast_lane_arr[:, 1],
    }).to_csv(ref_line_file, index=False)

    return track_full_name, track_file, ref_line_file, track_length


def build_occupancy_grid(track_file, cell_size, output_path, track_full_name):
    """Порт generate_track.ipynb cells 15-31 (occupancy grid), тот же upstream-код Track/in_quadrilateral."""
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from AssettoCorsaEnv.track import Track, in_quadrilateral

    track = Track(track_file)

    min_x = min(np.min(track.right_border_x), np.min(track.left_border_x)) - 1
    min_y = min(np.min(track.right_border_y), np.min(track.left_border_y)) - 1
    max_x = max(np.max(track.right_border_x), np.max(track.left_border_x)) + 1
    max_y = max(np.max(track.right_border_y), np.max(track.left_border_y)) + 1

    x_range = np.arange(min_x, max_x, cell_size)
    y_range = np.arange(min_y, max_y, cell_size)
    xx, yy = np.meshgrid(x_range, y_range)
    points = np.vstack([xx.ravel(), yy.ravel()]).T

    n_segments = track.num_segments - 1
    found_base = np.zeros(points.shape[0], dtype="bool")

    for segment in range(n_segments):
        corners = np.array([track.lr_track[0 + segment * 2:4 + segment * 2]])
        found_base = found_base + in_quadrilateral(corners, points)

    corners = np.concatenate([[track.lr_track[-2:]], [track.lr_track[:2]]], axis=1)
    found_base = found_base + in_quadrilateral(corners, points)
    found_base = found_base.astype("ubyte")

    track_map = {
        "cell_size": cell_size,
        "min_x": min_x, "min_y": min_y,
        "max_x": max_x, "max_y": max_y,
        "grid": found_base,
    }

    export_file = os.path.join(output_path, f"{track_full_name}_{cell_size}m.pkl")
    with open(export_file, "wb") as f:
        pickle.dump(track_map, f)

    return export_file, track


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ac-content", required=True, help=r"Путь к установке AC, напр. X:\SteamLibrarySSD\steamapps\common\assettocorsa")
    parser.add_argument("--track", required=True, help="Имя папки трассы в content/tracks, напр. magione")
    parser.add_argument("--track-configuration", default="", help="Подпапка layout, если есть (пусто для одноконфигурационных трасс)")
    parser.add_argument("--output", default=".", help="Куда писать csv/pkl (по умолчанию - текущая папка)")
    parser.add_argument("--cell-size", type=float, default=0.1, help="Размер ячейки occupancy grid, м")
    args = parser.parse_args()

    track_full_name, track_file, ref_line_file, track_length = export_track_and_racing_line(
        args.ac_content, args.track, args.track_configuration, args.output,
    )
    print(f"track_full_name={track_full_name}")
    print(f"track_file={track_file}")
    print(f"ref_line_file={ref_line_file}")
    print(f"track_length(from fast_lane.ai dist, ПРИБЛИЖЁННО - см. docstring)={track_length}")

    grid_file, _track = build_occupancy_grid(track_file, args.cell_size, args.output, track_full_name)
    print(f"grid_file={grid_file}")


if __name__ == "__main__":
    main()
