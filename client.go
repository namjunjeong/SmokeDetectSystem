package main

import (
	"bytes"
	"context"
	"image"
	"image/jpeg"
	"io"
	"log"
	"os"
	"os/exec"
	"strconv"
	"time"

	pb "github.com/namjunjeong/grpc_video_stream/proto"
	"github.com/namjunjeong/grpc_video_stream/utils"
	"github.com/stianeikeland/go-rpio/v4"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

func main() {
	video_name := os.Args[1]
	frame_rate := os.Args[2]
	frame_rate_int, _ := strconv.Atoi(frame_rate)

	_, err := exec.Command("ffmpeg", "-i", video_name, "-r", frame_rate+"/1", "%01d.jpeg").Output()
	if err != nil {
		log.Fatalf("exec error : %v", err)
	}

	conn, err := grpc.Dial(":50051", grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatalf("client connection error : %v", err)
	}
	defer conn.Close()

	client := pb.NewStreamingClient(conn)
	maxRecvSizeOption := grpc.MaxCallRecvMsgSize(32 * 10e6)
	maxCallSizeOption := grpc.MaxCallSendMsgSize(32 * 10e6)
	stream, err := client.ImgStream(context.Background(), maxRecvSizeOption, maxCallSizeOption)
	if err != nil {
		log.Fatalf("stream open error : %v", err)
	}
	ctx := stream.Context()
	done := make(chan bool)

	pinnum := []int{4, 17, 18, 27, 22, 23, 24, 25}
	rpiopin := make([]rpio.Pin, len(pinnum))
	err = rpio.Open()
	if err != nil {
		log.Fatalf("rpio open failed : %v", err)
	}
	for i, num := range pinnum {
		rpiopin[i] = rpio.Pin(num)
		rpiopin[i].Output()
		rpiopin[i].Low()
	}

	//sender function
	go func() {
		var img image.Image
		var i uint64 = 1
		var start, end time.Time
		var runtime int
		sleep_time := (1 / float64(frame_rate_int)) * 1000000000
		buf := new(bytes.Buffer)
		for {
			f, err := os.Open(strconv.FormatUint(i, 10) + ".jpeg")
			if err != nil {
				utils.Logger("load failed")
				break
			}
			img, _, _ = image.Decode(f)
			_ = jpeg.Encode(buf, img, nil)
			req := pb.Image{Id: i, Data: buf.Bytes()}
			if err := stream.Send(&req); err != nil {
				log.Fatalf("sending error : %v", err)
			}
			utils.Logger("image send")
			end = time.Now()
			runtime = int(end.Sub(start))
			time.Sleep((time.Duration(sleep_time) * time.Nanosecond) - (time.Duration(runtime) * time.Nanosecond))
			start = time.Now()
			buf.Reset()
			i++
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
			if smoke = response.Smoke; smoke == true {
				rpiopin[0].High()
			} else {
				rpiopin[0].Low()
			}
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
