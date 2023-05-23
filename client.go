package main

import (
	"bytes"
	"context"
	"io"
	"log"
	"os"
	"strconv"

	pb "github.com/namjunjeong/grpc_video_stream/proto"
	"github.com/namjunjeong/grpc_video_stream/utils"
	ffmpeg "github.com/u2takey/ffmpeg-go"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

func main() {
	video_name := os.Args[1]

	conn, err := grpc.Dial(":50051", grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatalf("client connection error : %v", err)
	}
	defer conn.Close()

	client := pb.NewStreamingClient(conn)
	stream, err := client.ImgStream(context.Background())
	if err != nil {
		log.Fatalf("stream open error : %v", err)
	}
	ctx := stream.Context()
	done := make(chan bool)

	//sender function
	go func() {
		var img_io io.Reader
		var i uint64
		var buf bytes.Buffer

		vid := ffmpeg.Input(video_name)
		for i = 1; i <= 10; i++ {
			img_io = utils.FrameToJpeg(vid, i*200)
			buf.ReadFrom(img_io)
			req := pb.Image{Id: i, Data: buf.Bytes()}
			if err := stream.Send(&req); err != nil {
				log.Fatalf("sending error : %v", err)
			}
			buf.Reset()
		}
		if err := stream.CloseSend(); err != nil {
			log.Fatalf("closing error : %v", err)
		}
	}()

	//receiver function
	go func() {
		var smoke bool
		for {
			response, err := stream.Recv()
			if err == io.EOF {
				close(done)
				return
			}
			if err != nil {
				log.Fatalf("receive error : %v", err)
			}
			smoke = response.Smoke
			utils.Logger("smoke state : " + strconv.FormatBool(smoke))
		}
	}()

	go func() {
		<-ctx.Done()
		if err := ctx.Err(); err != nil {
			utils.Logger("client closed")
		}
	}()

	<-done //block program until done

	utils.Logger("finished")
}
