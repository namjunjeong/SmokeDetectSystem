package utils

import (
	"fmt"
	"time"
)

func Logger(str string) {
	t := time.Now()
	query := string('[') + t.Format("2006-01-02T15:04:05.999") + "] : " + str
	fmt.Println(query)
}
