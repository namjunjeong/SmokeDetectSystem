package main

import (
	"bytes"
	"context"
	"image"
	"image/png"
	"io"
	"log"
	"os"
	"os/exec"
	"strconv"
	"time"

	pb "github.com/namjunjeong/grpc_video_stream/proto"
	"github.com/namjunjeong/grpc_video_stream/utils"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

func main() {
	video_name := os.Args[1]
	frame_rate := os.Args[2]
	frame_rate_int, _ := strconv.Atoi(frame_rate)

	_, err := exec.Command("ffmpeg", "-i", video_name, "-r", frame_rate+"/1", "%01d.png").Output()
	if err != nil {
		log.Fatalf("exec error : %v", err)
	}

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
		var img image.Image
		var i uint64 = 1
		buf := new(bytes.Buffer)

		for {
			f, err := os.Open(strconv.FormatUint(i, 10) + ".png")
			if err != nil {
				utils.Logger("load finished")
				break
			}
			img, _, _ = image.Decode(f)
			_ = png.Encode(buf, img)
			req := pb.Image{Id: i, Data: buf.Bytes()}
			if err := stream.Send(&req); err != nil {
				log.Fatalf("sending error : %v", err)
			}
			utils.Logger("image send")
			buf.Reset()
			i++
			time.Sleep(time.Duration(1/frame_rate_int) * time.Second)
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
