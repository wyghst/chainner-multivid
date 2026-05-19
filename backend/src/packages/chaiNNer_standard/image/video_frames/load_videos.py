from __future__ import annotations

from pathlib import Path

import numpy as np

from api import Generator, IteratorOutputInfo, NodeContext
from nodes.groups import Condition, if_group
from nodes.impl.ffmpeg import FFMpegEnv
from nodes.impl.video import VideoLoader
from nodes.properties.inputs import BoolInput, DirectoryInput, NumberInput
from nodes.properties.outputs import ImageOutput, NumberOutput, TextOutput
from nodes.utils.utils import split_file_path

from .. import video_frames_group

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".gif", ".m4v", ".wmv"}


@video_frames_group.register(
    schema_id="chainner:image:load_videos",
    name="Load Videos",
    description=[
        "Iterate over all frames in every video inside a folder.",
        "Yields each frame along with its frame index, video index, video name, and FPS.",
        "Connect Video Name to a Save Videos node so each input video produces a separate output file.",
        "Uses FFMPEG to read video files.",
    ],
    icon="MdVideoLibrary",
    inputs=[
        DirectoryInput(),
        BoolInput("Use limit", default=False).with_id(1),
        if_group(Condition.bool(1, True))(
            NumberInput("Limit per video", default=10, min=1)
            .with_docs("Limit the number of frames to iterate per video.")
            .with_id(2)
        ),
    ],
    outputs=[
        ImageOutput("Frame", channels=3),
        NumberOutput(
            "Frame Index",
            output_type="min(uint, max(0, IterOutput0.length - 1))",
        ).with_docs("Frame counter, resets to 0 at the start of each video."),
        NumberOutput("Video Index", output_type="uint").with_docs(
            "Counter that increments by 1 for each new video (starts at 0)."
        ),
        TextOutput("Video Name").with_docs(
            "Filename stem of the current video (no extension). Connect this to Save Videos so each input produces a separate output file."
        ),
        NumberOutput("FPS", output_type="0.."),
        NumberOutput("Total Videos", output_type="uint"),
    ],
    iterator_outputs=IteratorOutputInfo(outputs=[0, 1, 2, 3, 4]),
    node_context=True,
    side_effects=True,
    kind="generator",
)
def load_videos_node(
    node_context: NodeContext,
    directory: Path,
    use_limit: bool,
    limit: int,
) -> tuple[Generator[tuple[np.ndarray, int, int, str, float]], int]:
    paths = sorted(
        p
        for p in directory.iterdir()
        if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS
    )

    if not paths:
        raise ValueError(f"No video files found in {directory}")

    ffmpeg_env = FFMpegEnv.get_integrated(node_context.storage_dir)

    # Sum frame counts across all videos for accurate progress tracking.
    total_frames = 0
    for p in paths:
        loader = VideoLoader(p, ffmpeg_env)
        count = loader.metadata.frame_count
        if use_limit:
            count = min(count, limit)
        total_frames += count

    def iterator():
        for video_index, path in enumerate(paths):
            loader = VideoLoader(path, ffmpeg_env)
            video_name = split_file_path(path)[1]
            fps = loader.metadata.fps
            for frame_index, frame in enumerate(loader.stream_frames()):
                yield frame, frame_index, video_index, video_name, fps
                if use_limit and frame_index + 1 >= limit:
                    break

    return (
        Generator.from_iter(supplier=iterator, expected_length=total_frames),
        len(paths),
    )
