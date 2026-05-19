from __future__ import annotations

from pathlib import Path

import numpy as np

from api import Collector, IteratorInputInfo, KeyInfo, NodeContext
from nodes.groups import Condition, if_enum_group, if_group
from nodes.impl.ffmpeg import FFMpegEnv
from nodes.properties.inputs import (
    DirectoryInput,
    EnumInput,
    ImageInput,
    NumberInput,
    SliderInput,
    TextInput,
)
from nodes.properties.outputs import NumberOutput

from .. import video_frames_group
from .save_video import (
    PARAMETERS,
    AudioSettings,
    Simplicity,
    SimpleVideoFormat,
    VideoEncoder,
    VideoFormat,
    VideoPreset,
    Writer,
    get_simple_format,
)


def _open_writer(
    save_dir: Path,
    video_name: str,
    simplicity: Simplicity,
    container: VideoFormat,
    encoder: VideoEncoder,
    video_preset: VideoPreset,
    crf: int,
    additional_parameters: str | None,
    simple_video_format: SimpleVideoFormat,
    quality: int,
    fps: float,
    ffmpeg_env: FFMpegEnv,
) -> Writer:
    if simplicity == Simplicity.SIMPLE:
        container, encoder, video_preset, crf = get_simple_format(
            simple_video_format, quality
        )

    save_path = (save_dir / f"{video_name}.{container.ext}").resolve()
    save_path.parent.mkdir(parents=True, exist_ok=True)

    output_params: dict = {
        "filename": str(save_path),
        "pix_fmt": "yuv420p",
        "r": fps,
        "movflags": "faststart",
    }

    if encoder in container.encoders:
        output_params["vcodec"] = encoder.value
        parameters = PARAMETERS[encoder]
        if "preset" in parameters:
            output_params["preset"] = video_preset.value
        if "crf" in parameters:
            output_params["crf"] = crf

    global_params: list[str] = []
    if simplicity == Simplicity.ADVANCED and additional_parameters is not None:
        additional_parameters = " " + " ".join(additional_parameters.split())
        non_overridable = ["filename", "vcodec", "crf", "preset", "c:"]
        for parameter in additional_parameters.split(" -")[1:]:
            key, value = parameter, None
            try:
                key, value = parameter.split(" ")
            except Exception:
                pass
            if value is not None:
                for nop in non_overridable:
                    if not key.startswith(nop):
                        output_params[key] = value
                    else:
                        raise ValueError(f"Duplicate parameter: -{parameter}")
            else:
                global_params.append(f"-{parameter}")

    return Writer(
        container=container,
        encoder=encoder,
        fps=fps,
        audio=None,
        audio_settings=AudioSettings.AUTO,
        save_path=str(save_path),
        output_params=output_params,
        global_params=global_params,
        ffmpeg_env=ffmpeg_env,
    )


@video_frames_group.register(
    schema_id="chainner:image:save_videos",
    name="Save Videos",
    description=[
        "Writes frames from a Load Videos iterator into one output file per source video.",
        "Connect Video Name from Load Videos so the node detects when a new video starts and opens a new output file.",
        "Uses FFMPEG to write video files.",
    ],
    icon="MdVideoCameraBack",
    inputs=[
        ImageInput("Frame", channels=3),
        TextInput("Video Name", has_handle=True),
        DirectoryInput(must_exist=False).with_id(2),
        NumberInput("FPS", default=30, min=1, step=1, precision=4).with_id(14),
        EnumInput(Simplicity, default=Simplicity.SIMPLE, preferred_style="tabs")
        .with_id(16)
        .with_docs(
            "Simple mode offers a more user-friendly interface, while advanced mode allows more customization of FFMPEG options."
        ),
        if_enum_group(16, Simplicity.ADVANCED)(
            EnumInput(
                VideoFormat,
                label="Format",
                label_style="inline",
                option_labels={
                    VideoFormat.MKV: "mkv",
                    VideoFormat.MP4: "mp4",
                    VideoFormat.MOV: "mov",
                    VideoFormat.WEBM: "WebM",
                    VideoFormat.AVI: "avi",
                    VideoFormat.GIF: "GIF",
                },
            ).with_id(4),
            EnumInput(
                VideoEncoder,
                label="Encoder",
                label_style="inline",
                option_labels={
                    VideoEncoder.H264: "H.264 (AVC)",
                    VideoEncoder.H265: "H.265 (HEVC)",
                    VideoEncoder.VP9: "VP9",
                    VideoEncoder.FFV1: "FFV1",
                },
                conditions={
                    VideoEncoder.H264: Condition.enum(4, VideoEncoder.H264.formats),
                    VideoEncoder.H265: Condition.enum(4, VideoEncoder.H265.formats),
                    VideoEncoder.VP9: Condition.enum(4, VideoEncoder.VP9.formats),
                    VideoEncoder.FFV1: Condition.enum(4, VideoEncoder.FFV1.formats),
                },
            )
            .with_id(3)
            .wrap_with_conditional_group(),
            if_enum_group(3, (VideoEncoder.H264, VideoEncoder.H265))(
                EnumInput(
                    VideoPreset,
                    label="Preset",
                    label_style="inline",
                    default=VideoPreset.MEDIUM,
                ).with_id(8),
            ),
            if_enum_group(3, (VideoEncoder.H264, VideoEncoder.H265, VideoEncoder.VP9))(
                SliderInput("CRF", min=0, max=51, default=23, ends=("Best", "Worst")).with_id(9),
            ),
            TextInput(
                "Additional parameters",
                multiline=True,
                allow_empty_string=True,
                has_handle=False,
            )
            .make_optional()
            .with_id(13),
        ),
        if_enum_group(16, Simplicity.SIMPLE)(
            EnumInput(
                SimpleVideoFormat,
                label="Video Format",
                option_labels={
                    SimpleVideoFormat.MP4_H264: "MP4 (H.264/AVC)",
                    SimpleVideoFormat.MP4_H265: "MP4 (H.265/HEVC)",
                    SimpleVideoFormat.WEBM: "WebM",
                    SimpleVideoFormat.GIF: "GIF",
                },
            ).with_id(17),
            if_group(~Condition.enum(17, SimpleVideoFormat.GIF))(
                SliderInput("Quality", min=0, max=100, default=75).with_id(18),
            ),
        ),
    ],
    iterator_inputs=IteratorInputInfo(inputs=[0, 1]),
    outputs=[
        NumberOutput("Videos Saved", output_type="uint"),
    ],
    key_info=KeyInfo.enum(4),
    kind="collector",
    side_effects=True,
    node_context=True,
)
def save_videos_node(
    node_context: NodeContext,
    _frame: None,
    _video_name: None,
    save_dir: Path,
    fps: float,
    simplicity: Simplicity,
    container: VideoFormat,
    encoder: VideoEncoder,
    video_preset: VideoPreset,
    crf: int,
    additional_parameters: str | None,
    simple_video_format: SimpleVideoFormat,
    quality: int,
) -> Collector[tuple[np.ndarray, str], int]:
    ffmpeg_env = FFMpegEnv.get_integrated(node_context.storage_dir)
    writer: Writer | None = None
    current_name: str | None = None
    videos_saved = 0

    def on_iterate(inputs: tuple[np.ndarray, str]):
        nonlocal writer, current_name, videos_saved

        frame, video_name = inputs

        if video_name != current_name:
            if writer is not None:
                writer.close()
                videos_saved += 1
            current_name = video_name
            writer = _open_writer(
                save_dir=save_dir,
                video_name=video_name,
                simplicity=simplicity,
                container=container,
                encoder=encoder,
                video_preset=video_preset,
                crf=crf,
                additional_parameters=additional_parameters,
                simple_video_format=simple_video_format,
                quality=quality,
                fps=fps,
                ffmpeg_env=ffmpeg_env,
            )

        assert writer is not None
        writer.write_frame(frame)

    def on_complete() -> int:
        nonlocal writer, videos_saved
        if writer is not None:
            writer.close()
            videos_saved += 1
        return videos_saved

    return Collector(on_iterate=on_iterate, on_complete=on_complete)
