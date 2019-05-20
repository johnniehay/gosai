package gosai
import "C"

/*
#include <sai/sai.h>
*/
//import "C"

func PrintSuc() {
	//a := C.SAI_STATUS_SUCESS
	a := "SAI_STATUS_SUCESS"
	println(a)
}