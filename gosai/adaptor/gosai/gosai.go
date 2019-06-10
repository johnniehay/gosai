package gosai
// #cgo CFLAGS: -I ../../../SAI/inc -I../../ -I../gen-inc
// #cgo LDFLAGS: -L${SRCDIR}/../cmake-build-debug -ladaptor
// #cgo LDFLAGS: -L/home/johnnie/MEGA/code/gosai/lib/x86_64-linux-gnu -lsai -Wl,-unresolved-symbols=ignore-in-shared-libs
/*
#include "sai_adaptor.h"
*/
import "C"
import (
	"fmt"
	"unsafe"
)

func InitGoSai() SaiStatus {
	var saiRet SaiStatus
	saiRet = SaiStatus(C.sai_api_initialize(0,nil))
	if saiRet != SaiStatus(SAI_STATUS_SUCCESS) {
		fmt.Println("Error sai_api_initialize failed with ",saiRet)
		return SaiStatus(SAI_STATUS_FAILURE)
	}
	saiRet = SaiStatus(C.sai_api_tbl_init())
	/*if saiRet != SAI_STATUS_SUCCESS {
		fmt.Println("Error sai_api_tbl_init failed with ",saiRet)
		return SAI_STATUS_FAILURE
	}*/
	return SaiStatus(SAI_STATUS_SUCCESS)
}

func SaiSwitchIdQuery(objId SaiObjectId) SaiObjectId {
	retObjId := C.sai_switch_id_query(objId.C())
	return SaiObjectId(retObjId)
}
func SaiObjectTypeQuery(objId SaiObjectId) SaiInt32 {
	objType := C.sai_object_type_query(objId.C())
	return SaiInt32(objType)
}
/*
noAction: sai_flush_fdb_entries //Done
noAction: sai_recv_hostif_packet //Done
noAction: sai_send_hostif_packet //Done
noAction: sai_bulk_create_route_entry //Pointer-pointer parameters
noAction: sai_bulk_remove_route_entry
noAction: sai_bulk_set_route_entry_attribute
noAction: sai_bulk_get_route_entry_attribute
Skipping: sai_clear_port_all_stats sai_object_id_t //Done
Skipping: sai_get_tam_snapshot_stats sai_object_id_t //Not implemented, future removed
*/

//sai_status_t sai_flush_fdb_entries_fn)(_In_ sai_object_id_t switch_id,_In_ uint32_t attr_count,_In_ const sai_attribute_t *attr_list);
func SaiFlushFdbEntries(switchId SaiObjectId, attrlist SaiAttributeList) SaiStatus {
	count, list := attrlist.C()
	retstatus := C.sai_flush_fdb_entries(switchId.C(),count,list)
	return SaiStatus(retstatus)
}
//sai_status_t sai_send_hostif_packet(sai_object_id_t hostif_id, sai_size_t buffer_size, const void *buffer, uint32_t attr_count, const sai_attribute_t *attr_list)
func SaiSendHostifPacket(hostifId SaiObjectId, buffer []byte, attrlist SaiAttributeList) SaiStatus {
	attrCount, attrList := attrlist.C()
	buflen := C.sai_size_t(len(buffer))
	retstatus := C.sai_send_hostif_packet(hostifId.C(),buflen,unsafe.Pointer(&buffer[0]),attrCount, attrList)
	return SaiStatus(retstatus)
}
func generateHostifPacketAttributeList(cAttrs[]C.sai_attribute_t) SaiAttributeList{
	attrs := make(SaiAttributeList,len(cAttrs))
	for i, attr := range cAttrs {
		switch attr.id {
		case SaiHostifPacketAttrHostifTrapId,
			SaiHostifPacketAttrIngressPort,
			SaiHostifPacketAttrIngressLag,
			SaiHostifPacketAttrEgressPortOrLag,
			SaiHostifPacketAttrBridgeId:
				attrs[i].Value = new(SaiObjectId)
		case SaiHostifPacketAttrHostifTxType:
			attrs[i].Value = new(SaiInt32)
		case SaiHostifPacketAttrTimestamp:
			attrs[i].Value = &SaiTimespec{}
		default:
			panic("Unknown Id for HostifPacketAttribute")
		}
	}
	attrs.fromC(C.uint32_t(len(cAttrs)),(*C.sai_attribute_t)(unsafe.Pointer(&cAttrs[0])))
	return attrs
}

//sai_status_t sai_recv_hostif_packet(sai_object_id_t hostif_id, sai_size_t *buffer_size, void *buffer, uint32_t *attr_count, sai_attribute_t *attr_list)
func SaiRecvHostifPacket(hostifId SaiObjectId) ([]byte,SaiAttributeList,SaiStatus) {
	bufsize := C.sai_size_t(0)
	attrCount := C.uint32_t(0)
	retstatus := C.sai_recv_hostif_packet(hostifId.C(),&bufsize,nil,&attrCount, nil)
	if C.long(retstatus) == SAI_STATUS_BUFFER_OVERFLOW {
		buffer := make([]byte,bufsize)
		attrList := make([]C.sai_attribute_t,attrCount)
		retstatus := C.sai_recv_hostif_packet(hostifId.C(),&bufsize,unsafe.Pointer(&buffer[0]),&attrCount, &attrList[0])
		return buffer,generateHostifPacketAttributeList(attrList),SaiStatus(retstatus)
	}
	return make([]byte,0,0),make([]SaiAttribute,0,0),SaiStatus(retstatus)
}

func SaiClearPortAllStats(objId SaiObjectId) SaiStatus {
	retStatus := C.sai_clear_port_all_stats(objId.C())
	return SaiStatus(retStatus)
}