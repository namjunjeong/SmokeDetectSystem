package utils

import (
	"bytes"
	"fmt"
	"io"

	ffmpeg "github.com/u2takey/ffmpeg-go"
	ffmpeg_go "github.com/u2takey/ffmpeg-go"
)

func FrameToJpeg(file *ffmpeg_go.Stream, frameNum uint64) io.Reader {
	buf := bytes.NewBuffer(nil)
	err := file.
		Filter("select", ffmpeg.Args{fmt.Sprintf("gte(n,%d)", frameNum)}).
		Output("pipe:", ffmpeg.KwArgs{"vframes": 1, "format": "image2", "vcodec": "mjpeg"}).
		WithOutput(buf).
		Run()
	if err != nil {
		panic(err)
	}
	return buf
}
