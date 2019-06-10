package main

import "C"
import (
	"encoding/binary"
	"fmt"
	"github.com/davecgh/go-spew/spew"
	"github.com/johnniehay/gosai/gosai/adaptor/gosai"
	"net"
)

type test1 struct {
	a int64
	b bool
}

type testarr []test1

func TestGoSai() {
	spew.Println("InitGoSai",gosai.InitGoSai())
	//objid,sairet := gosai.SaiCreateVlan(0x21000000000000,gosai.SaiAttributeList{gosai.SaiAttribute{gosai.SaiAttrId(0),gosai.SaiUint16(32)}})
	//objid,sairet := gosai.SaiCreatePort(0x21000000000000,gosai.SaiAttributeList{gosai.SaiAttribute{gosai.SaiAttrId(2),&gosai.SaiS32List{1,2,3}}})
	SaiBoolTrue := gosai.SaiBool(true)
	//SaiBoolFalse := gosai.SaiBool(false)
	srcMacBytes , _:= net.ParseMAC("00:01:04:4C:49:F5")
	srcMac := gosai.ByteSliceToSaiMac(srcMacBytes)
	swOid,sairet := gosai.SaiCreateSwitch(gosai.SaiAttributeList{gosai.SaiAttribute{gosai.SaiSwitchAttrInitSwitch,&SaiBoolTrue},
												gosai.SaiAttribute{gosai.SaiSwitchAttrSrcMacAddress,&srcMac}})
	spew.Printf("SaiCreateSwitch %#x %#x %v\n", swOid,sairet, gosai.SaiObjectTypeQuery(swOid))
	vrOid := gosai.SaiObjectId(99)
	sairet = gosai.SaiGetSwitchAttribute(swOid,&gosai.SaiAttributeList{gosai.SaiAttribute{gosai.SaiSwitchAttrDefaultVirtualRouterId,&vrOid}})
	spew.Printf("SaiGetSwitchAttribute:SaiSwitchAttrDefaultVirtualRouterId %#x %#x %v\n", vrOid,sairet,gosai.SaiObjectTypeQuery(vrOid))
	cpuportOid := gosai.SaiObjectId(0)
	sairet = gosai.SaiGetSwitchAttribute(swOid,&gosai.SaiAttributeList{gosai.SaiAttribute{gosai.SaiSwitchAttrCpuPort,&cpuportOid}})
	spew.Printf("SaiGetSwitchAttribute:SaiSwitchAttrCpuPort %#x %#x %v\n", cpuportOid,sairet,gosai.SaiObjectTypeQuery(cpuportOid))
	numActivePorts := gosai.SaiUint32(0)
	sairet = gosai.SaiGetSwitchAttribute(swOid,&gosai.SaiAttributeList{gosai.SaiAttribute{gosai.SaiSwitchAttrNumberOfActivePorts,&numActivePorts}})
	spew.Printf("SaiGetSwitchAttribute:SaiSwitchAttrNumberOfActivePorts %#v %v\n", numActivePorts,sairet)
	portList := make(gosai.SaiObjectList,numActivePorts)
	sairet = gosai.SaiGetSwitchAttribute(swOid,&gosai.SaiAttributeList{gosai.SaiAttribute{gosai.SaiSwitchAttrPortList,&portList}})
	spew.Printf("SaiGetSwitchAttribute:SaiSwitchAttrPortList %#x %v\n", portList,sairet)
	portHwLaneLists := make([]gosai.SaiU32List,numActivePorts)
	spew.Printf("portHwLaneLists: %+#v",portHwLaneLists)
	for i, portOid := range portList {
		portHwLaneLists[i] = make(gosai.SaiU32List,8)
		sairet = gosai.SaiGetPortAttribute(portOid,&gosai.SaiAttributeList{gosai.SaiAttribute{gosai.SaiPortAttrHwLaneList,&portHwLaneLists[i]}})
		spew.Printf("SaiGetPortAttribute:SaiPortAttrHwLaneList %v len %v %v\n",portHwLaneLists[i],len(portHwLaneLists[i]),sairet)
	}
	defaultBridgeOid := gosai.SaiObjectId(0)
	defaultVlanOid := gosai.SaiObjectId(0)
	sairet = gosai.SaiGetSwitchAttribute(swOid,&gosai.SaiAttributeList{gosai.SaiAttribute{gosai.SaiSwitchAttrDefault1qBridgeId,&defaultBridgeOid},
								gosai.SaiAttribute{gosai.SaiSwitchAttrDefaultVlanId,&defaultVlanOid}})
	spew.Printf("SaiGetSwitchAttribute:SaiSwitchAttrDefault1qBridgeId %#x:SaiSwitchAttrDefaultVlanId %#x %v\n", defaultBridgeOid,defaultVlanOid,sairet)
	vlanMemberList := make(gosai.SaiObjectList,numActivePorts)
	sairet = gosai.SaiGetVlanAttribute(defaultVlanOid,&gosai.SaiAttributeList{gosai.SaiAttribute{gosai.SaiVlanAttrMemberList,&vlanMemberList}})
	spew.Printf("SaiGetVlanAttribute:SaiVlanAttrMemberList %#x %v\n", vlanMemberList,sairet)
	for _, vlanMemberOid := range vlanMemberList {
		sairet = gosai.SaiRemoveVlanMember(vlanMemberOid)
		spew.Printf("SaiRemoveVlanMember(%#x) %v\n", vlanMemberOid,sairet)
	}
	bridgePortList := make(gosai.SaiObjectList,numActivePorts+1)
	sairet = gosai.SaiGetBridgeAttribute(defaultBridgeOid,&gosai.SaiAttributeList{gosai.SaiAttribute{gosai.SaiBridgeAttrPortList,&bridgePortList}})
	spew.Printf("SaiGetVlanAttribute:SaiVlanAttrMemberList %#x %v\n", bridgePortList,sairet)
	for _, bridgePortOid := range bridgePortList {
		bridgePortType := gosai.SaiInt32(0)
		sairet = gosai.SaiGetBridgePortAttribute(bridgePortOid,&gosai.SaiAttributeList{gosai.SaiAttribute{gosai.SaiBridgePortAttrType,&bridgePortType}})
		if sairet == gosai.SAI_STATUS_SUCCESS && bridgePortType == gosai.SaiBridgePortTypePort {
			sairet = gosai.SaiRemoveBridgePort(bridgePortOid)
			spew.Printf("SaiRemoveBridgePort(%#x) %v\n", bridgePortOid,sairet)
		} else {
			spew.Printf("SaiGetBridgePortAttribute:SaiBridgePortAttrType %v %v\n", bridgePortOid,sairet)
		}
	}
	//2019-06-03.18:24:16.381792|c|SAI_OBJECT_TYPE_ROUTE_ENTRY:{"dest":"0.0.0.0/0","switch_id":"oid:0x21000000000000","vr":"oid:0x3000000000066"}|SAI_ROUTE_ENTRY_ATTR_PACKET_ACTION=SAI_PACKET_ACTION_DROP
	//2019-06-03.18:24:16.383994|c|SAI_OBJECT_TYPE_ROUTE_ENTRY:{"dest":"::/0","switch_id":"oid:0x21000000000000","vr":"oid:0x3000000000066"}|SAI_ROUTE_ENTRY_ATTR_PACKET_ACTION=SAI_PACKET_ACTION_DROP
	routeEntries := make([]gosai.SaiRouteEntry,0)
	packetActionDrop := gosai.SaiInt32(gosai.SaiPacketActionDrop)
	attrsPacketDrop := gosai.SaiAttributeList{gosai.SaiAttribute{gosai.SaiRouteEntryAttrPacketAction, &packetActionDrop}}
	_,ipnet0,_ := net.ParseCIDR("0.0.0.0/0")
	sairet = createIPv4RouteEntry(*ipnet0,attrsPacketDrop,swOid, vrOid, &routeEntries)
	spew.Printf("createIPv4RouteEntry %v %v %v %v\n",ipnet0,attrsPacketDrop,routeEntries,sairet)
	_,ip6net0,_ := net.ParseCIDR("::/0")
	sairet = createIPv6RouteEntry(*ip6net0,attrsPacketDrop,swOid, vrOid, &routeEntries)
	spew.Printf("createIPv6RouteEntry %v %v %v %v\n",ip6net0,attrsPacketDrop,routeEntries,sairet)
	hostiftblentryTypeWildcard := gosai.SaiInt32(gosai.SaiHostifTableEntryTypeWildcard)
	hostiftblentryChannelTypeNetdevPhy := gosai.SaiInt32(gosai.SaiHostifTableEntryChannelTypeNetdevPhysicalPort)
	hostiftblentryOid, sairet := gosai.SaiCreateHostifTableEntry(swOid,gosai.SaiAttributeList{gosai.SaiAttribute{gosai.SaiHostifTableEntryAttrType,&hostiftblentryTypeWildcard},
					gosai.SaiAttribute{gosai.SaiHostifTableEntryAttrChannelType,&hostiftblentryChannelTypeNetdevPhy}})
	spew.Printf("SaiCreateHostifTableEntry %#x %v\n", hostiftblentryOid,sairet)
	defaultTrapGroupOid := gosai.SaiObjectId(99)
	sairet = gosai.SaiGetSwitchAttribute(swOid,&gosai.SaiAttributeList{gosai.SaiAttribute{gosai.SaiSwitchAttrDefaultTrapGroup,&defaultTrapGroupOid}})
	spew.Printf("SaiGetSwitchAttribute:SaiSwitchAttrDefaultTrapGroup %#x %v\n", defaultTrapGroupOid,sairet)
	//|c|SAI_OBJECT_TYPE_HOSTIF_TRAP:oid:0x2200000000006a|SAI_HOSTIF_TRAP_ATTR_TRAP_TYPE=SAI_HOSTIF_TRAP_TYPE_TTL_ERROR|SAI_HOSTIF_TRAP_ATTR_PACKET_ACTION=SAI_PACKET_ACTION_TRAP|SAI_HOSTIF_TRAP_ATTR_TRAP_GROUP=oid:0x11000000000067|SAI_HOSTIF_TRAP_ATTR_TRAP_PRIORITY=0
	hostifTrapTTLErrorOid, sairet := gosai.SaiCreateHostifTrap(swOid,gosai.SaiAttributeList{
		gosai.SaiAttribute{gosai.SaiHostifTrapAttrTrapType,EnumVal(gosai.SaiHostifTrapTypeTtlError)},
		gosai.SaiAttribute{gosai.SaiHostifTrapAttrPacketAction, EnumVal(gosai.SaiPacketActionTrap)},
		gosai.SaiAttribute{gosai.SaiHostifTrapAttrTrapGroup, &defaultTrapGroupOid},
		gosai.SaiAttribute{gosai.SaiHostifTrapAttrTrapPriority, EnumVal(0)}})
	spew.Printf("SaiCreateHostifTrap:TtlError %#x %v\n", hostifTrapTTLErrorOid,sairet)
	//|c|SAI_OBJECT_TYPE_ACL_TABLE:oid:0x700000000006b|SAI_ACL_TABLE_ATTR_ACL_BIND_POINT_TYPE_LIST=1:SAI_ACL_BIND_POINT_TYPE_PORT|SAI_ACL_TABLE_ATTR_ACL_STAGE=SAI_ACL_STAGE_INGRESS|SAI_ACL_TABLE_ATTR_FIELD_ECN=true|SAI_ACL_TABLE_ATTR_FIELD_DSCP=true
	//|c|SAI_OBJECT_TYPE_ACL_ENTRY:oid:0x800000000006c|SAI_ACL_ENTRY_ATTR_TABLE_ID=oid:0x700000000006b|SAI_ACL_ENTRY_ATTR_PRIORITY=1000|SAI_ACL_ENTRY_ATTR_FIELD_ECN=0&mask:0x3|SAI_ACL_ENTRY_ATTR_FIELD_DSCP=8&mask:0x3f|SAI_ACL_ENTRY_ATTR_ACTION_SET_PACKET_COLOR=SAI_PACKET_COLOR_YELLOW
	//|c|SAI_OBJECT_TYPE_ACL_ENTRY:oid:0x800000000006d|SAI_ACL_ENTRY_ATTR_TABLE_ID=oid:0x700000000006b|SAI_ACL_ENTRY_ATTR_PRIORITY=999|SAI_ACL_ENTRY_ATTR_FIELD_ECN=0&mask:0x3|SAI_ACL_ENTRY_ATTR_FIELD_DSCP=0&mask:0x3f|SAI_ACL_ENTRY_ATTR_ACTION_SET_PACKET_COLOR=SAI_PACKET_COLOR_YELLOW
	aclTableColorOid, sairet := gosai.SaiCreateAclTable(swOid,gosai.SaiAttributeList{
		gosai.SaiAttribute{gosai.SaiAclTableAttrAclBindPointTypeList,EnumVal(1)},
		gosai.SaiAttribute{gosai.SaiAclTableAttrAclStage, EnumVal(gosai.SaiAclStageIngress)},
		gosai.SaiAttribute{gosai.SaiAclTableAttrFieldEcn, &SaiBoolTrue},
		gosai.SaiAttribute{gosai.SaiAclTableAttrFieldDscp, &SaiBoolTrue}})
	spew.Printf("SaiCreateAclTable:aclTableColorOid %#x %v\n", aclTableColorOid,sairet)
	uint8_3f := gosai.SaiUint8(0x3f)
	uint8_3 := gosai.SaiUint8(0x3)
	uint8_8 := gosai.SaiUint8(0x8)
	aclColor08Oid, sairet := gosai.SaiCreateAclEntry(swOid,gosai.SaiAttributeList{
		gosai.SaiAttribute{gosai.SaiAclEntryAttrTableId,&aclTableColorOid},
		gosai.SaiAttribute{gosai.SaiAclEntryAttrPriority, EnumVal(1000)},
		gosai.SaiAttribute{gosai.SaiAclEntryAttrFieldEcn, &gosai.SaiAclFieldData{SaiBoolTrue.C(),&uint8_3,new(gosai.SaiUint8)}},
		gosai.SaiAttribute{gosai.SaiAclEntryAttrFieldDscp, &gosai.SaiAclFieldData{SaiBoolTrue.C(),&uint8_3f,&uint8_8}},
		gosai.SaiAttribute{gosai.SaiAclEntryAttrActionSetPacketColor, EnumVal(gosai.SaiPacketColorYellow)}})
	spew.Printf("SaiCreateAclEntry:aclColor08Oid %#x %v\n", aclColor08Oid,sairet)
	aclColor00Oid, sairet := gosai.SaiCreateAclEntry(swOid,gosai.SaiAttributeList{
		gosai.SaiAttribute{gosai.SaiAclEntryAttrTableId,&aclTableColorOid},
		gosai.SaiAttribute{gosai.SaiAclEntryAttrPriority, EnumVal(999)},
		gosai.SaiAttribute{gosai.SaiAclEntryAttrFieldEcn, &gosai.SaiAclFieldData{SaiBoolTrue.C(),&uint8_3,new(gosai.SaiUint8)}},
		gosai.SaiAttribute{gosai.SaiAclEntryAttrFieldDscp, &gosai.SaiAclFieldData{SaiBoolTrue.C(),&uint8_3f,new(gosai.SaiUint8)}},
		gosai.SaiAttribute{gosai.SaiAclEntryAttrActionSetPacketColor, EnumVal(gosai.SaiPacketColorYellow)}})
	spew.Printf("SaiCreateAclEntry:aclColor00Oid %#x %v\n", aclColor00Oid,sairet)
	aclEntryMinPriority := gosai.SaiUint32(0)
	aclEntryMaxPriority := gosai.SaiUint32(0)
	sairet = gosai.SaiGetSwitchAttribute(swOid,&gosai.SaiAttributeList{
		gosai.SaiAttribute{gosai.SaiSwitchAttrAclEntryMinimumPriority,&aclEntryMinPriority},
		gosai.SaiAttribute{gosai.SaiSwitchAttrAclEntryMaximumPriority,&aclEntryMaxPriority}})
	spew.Printf("SaiGetSwitchAttribute:SaiSwitchAttrAclEntryPriorities min:%v max:%v %v\n", aclEntryMinPriority,aclEntryMaxPriority,sairet)
}

func createIPv4RouteEntry(ipNet net.IPNet,attrs gosai.SaiAttributeList,swOid gosai.SaiObjectId, vrOid gosai.SaiObjectId, routeEntries *[]gosai.SaiRouteEntry) gosai.SaiStatus {
	ipAddr := gosai.SaiIp4(binary.BigEndian.Uint32(ipNet.IP))
	ipAddrMask := gosai.SaiIp4(binary.BigEndian.Uint32(ipNet.Mask))
	routeEntry := gosai.SaiRouteEntry{swOid, vrOid, gosai.SaiIpPrefix{gosai.SaiIpAddrFamilyIpv4, &ipAddr, &ipAddrMask}}
	sairet := gosai.SaiCreateRouteEntry(routeEntry, attrs)
	if sairet != gosai.SAI_STATUS_SUCCESS {
		return gosai.SaiStatus(sairet)
	}
	*routeEntries = append(*routeEntries, routeEntry)
	return gosai.SaiStatus(sairet)
}
func createIPv6RouteEntry(ipNet net.IPNet,attrs gosai.SaiAttributeList,swOid gosai.SaiObjectId, vrOid gosai.SaiObjectId, routeEntries *[]gosai.SaiRouteEntry) gosai.SaiStatus {
	ipAddr := gosai.ByteSliceToSaiIp6(ipNet.IP.To16())
	ipAddrMask := gosai.ByteSliceToSaiIp6(ipNet.Mask)
	routeEntry := gosai.SaiRouteEntry{swOid, vrOid, gosai.SaiIpPrefix{gosai.SaiIpAddrFamilyIpv6, &ipAddr, &ipAddrMask}}
	sairet := gosai.SaiCreateRouteEntry(routeEntry, attrs)
	if sairet != gosai.SAI_STATUS_SUCCESS {
		return gosai.SaiStatus(sairet)
	}
	*routeEntries = append(*routeEntries, routeEntry)
	return gosai.SaiStatus(sairet)
}

func EnumVal(v int) *gosai.SaiInt32 {
	castv := gosai.SaiInt32(v)
	return &castv
}

func main() {
	//gosai.PrintSuc()
	//su16 := gosai.SaiUint16(12)
	//a := gosai.SaiAttr(19,&su16)
	//sa := testarr{{a:6,b:false}}
	//sa = append(sa,test1{1,true})
	//sa = append(sa,test1{5,false})
	//b := a.id
	//spew.Println("id:{}",b)
	//spew.Println("a:{}",a)
	//spew.Println("sa:{}",sa)
	//i := gosai.SaiIp4(binary.BigEndian.Uint32(net.ParseIP("127.0.0.1")))

	//si4 := gosai.SaiIp6(net.ParseIP("::1").To6())
	//b := [16]byte{1,2,0,0,0,0,0,0,0,0,0,0,0,0,0,3}
	b := net.ParseIP("2001:4200:7000::1").To16()
	//var attrval C.sai_attribute_value_t = *((*C.sai_attribute_value_t)(unsafe.Pointer(&v)))
	//var si6 gosai.SaiIp6 = *((*gosai.SaiIp6)(unsafe.Pointer(&b[0])))
	//var si6 gosai.SaiIp6 = gosai.SaiIp6(gosai.ByteSlice(b).ToSaiIp6())
	var si6 gosai.SaiIp6 = gosai.SaiIp6(gosai.ByteSliceToSaiIp6(b))
	var hmac gosai.SaiHmac = gosai.SaiHmac{8,[8]gosai.SaiUint32{1,2,3,4,5,6,7,8}}
	//var si6 gosai.SaiIp6 = *((*gosai.SaiIp6)(&b[0]))
	att := gosai.SaiAttribute{1,&gosai.SaiTlvList{gosai.SaiTlv{0,&hmac}}}
	attc := att.C()
	spew.Printf("att: %#+v\n",att)
	spew.Printf("attc: %#v\n",attc)
	attfrom := (&gosai.SaiAttribute{2,&gosai.SaiTlvList{gosai.SaiTlv{5,&gosai.SaiHmac{18,[8]gosai.SaiUint32{9,12,13,14,15,16,17,18}}}}}).C()
	spew.Printf("attfrom: %#v\n",attfrom)
	//att.FromC(attfrom)
	//ipa := gosai.SaiIp4{}.(gosai.SaiIpAddr)
	//spew.Println("ip:{}",ipa)
	//spew.Println("si4:{}",si4)
	//spew.Printf("nip:%#v\n",nip)
	const a = -0x00000001
	ipaddress := gosai.SaiIpAddress{1,&si6}
	spew.Printf("ipaddress: %#+v\n",ipaddress)
	fmt.Printf("ipaddress: %#v\n",ipaddress)
	fmt.Printf("ipaddress: %#v\n",int(a))
	spew.Printf("si6:%T %#v\n",si6.C(),si6.C())
	spew.Printf("hmac:%T %#v\n",hmac.C(),hmac.C())
	spew.Printf("att: %#v \n",att.C())

	TestGoSai()
}
