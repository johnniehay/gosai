from collections import defaultdict

from api_tbl_gen import *
from gen_c_adaptor import gen_c_func_adaptor

saiinc = '/home/johnnie/MEGA/code/gosai/SAI/inc/'


class AdaptorVisitor(c_ast.NodeVisitor):
    def __init__(self):
        self.adaptorast = c_ast.FileAST(list([]))

    def visit_Enum(self, node):
        print('Enum %s at %s' % (node.name, node.coord))

    def visit_FuncDecl(self, node):
        if node.type is c_ast.TypeDecl:
            print('%s at %s' % (node.type.declname, node.coord))
        self.adaptorast.ext.append(node)

    def visit_Typedef(self, node):
        # print('%s type %s at %s' % (node.name,node.type, node.coord))
        if 'fn' in node.name:
            print('%s storage %s at %s' % (node.name, node.storage, node.coord))
            self.adaptorast.ext.append(node)
        self.visit(node.type)


generator = c_generator.CGenerator()
ast = parse_file(saiinc + 'sai.h', use_cpp=True,
                 cpp_args=[r"-I" + saiinc, r"-Ifake_libc_include", r"-D __attribute__(x)="])
ast.ext = [extdef for extdef in ast.ext if not 'fake' in extdef.coord.file]
astperfile = defaultdict(list)
for extdef in ast.ext:
    astperfile[extdef.coord.file].append(extdef)
file_ast = astperfile['/home/johnnie/MEGA/code/gosai/SAI/inc/saimpls.h']

saih_ast = astperfile['/home/johnnie/MEGA/code/gosai/SAI/inc/sai.h']
sai_api_t = [extdef for extdef in saih_ast if 'sai_api_t' == extdef.name]
if len(sai_api_t) != 1:
    print("Error:sai_api_t not found")
sai_api_t = sai_api_t[0]
sai_api_enum = [api.name for api in sai_api_t.type.type.values.enumerators][1:-1]
sai_apis = [api[8:].lower() for api in sai_api_enum]
generate_sai_api_tbl_h(sai_apis)
generate_sai_api_tbl_init_c(sai_apis, sai_api_enum)

c_func_adaptor_defs = gen_c_func_adaptor(astperfile)


def ctomixedcase(n, replace="PT",export=True):
    outstr = ""
    capnext = export
    if "P" in replace and (isPrimitive(n) or isEnum(n)):
        return "C." + n
    if "T" in replace and "_t" == n[-2:]:
        n = n[:-2]
    for l in n:
        if l == "_":
            capnext = True
            continue
        if capnext:
            outstr += l.upper()
            capnext = False
        else:
            outstr += l
    return outstr


listStructToC = r'''
func (v *{0}) C() C.{1} {{
    cv := make([]C.{2},len(*v))
    for i, val := range *v {{
        cv[i] = C.{2}(val{3})
    }}
	liststruct  := C.{1}{{C.uint(len(*v)),((*C.{2})(unsafe.Pointer(&cv[0])))}}
	return liststruct
}}
'''  # GoListType,CListType,CElementType,toCfunc
listStructFromCold = r'''
func (v *{0}) fromC(s C.{1}) {{
	clen := int(s.count)
	vlen := len(*v)
	if vlen < clen {{
		nv := make([]{3},clen,clen)
		copy(nv,*v)
		*v = nv
	}}
	cslice := (*[1 << 28]C.{2})(unsafe.Pointer(s.list))[:clen:clen]
	for i, val := range cslice {{
		(*v)[i]{4}(val)
	}}
}}
'''  # GoListType,CListType,CElementType,GoElementType,fromfunc
listStructFromC = r'''
func (v *{0}) fromC(s C.{1}) {{
	clen := int(s.count)
	vlen := len(*v)
	if vlen != clen {{
		nv := make([]{3},clen,clen)
		copy(nv,*v)
		*v = nv
	}}
	cslice := (*[1 << 28]C.{2})(unsafe.Pointer(s.list))[:clen:clen]
	for i, val := range cslice {{
		(*v)[i]{4}(val)
	}}
}}
'''  # GoListType,CListType,CElementType,GoElementType,fromfunc
StructTemplate = r'''
type {0} struct {{ {1}
}}
'''  # GoType,GoStructFields
StructFieldTemplate = r'''
	{0} {1}'''  # GoFieldName,GoFieldType
StructFieldAssign = r'''{0}:(*v).{1}{2},'''  # DstFieldName,SrcFieldType,SrcFieldFuncCall
StructFieldArrAssign = r'''{0}:{1},'''  # DstFieldName,SrcVar
# var Hmac [8]C.sai_uint32_t = *((*[8]C.sai_uint32_t)(unsafe.Pointer(&(v.Hmac[0]))))
StructFieldArrAssignConv = '''\n	var {0} {1} = *((*{1})(unsafe.Pointer(&(v.{2}[0]))))'''  # DstFieldName,DstFieldType SrcFieldArrName
StructFieldFromC = '''v.{0}{1}(s.{2})\n'''  # DstFieldName,DstFieldFromFunc,SrcFieldName
# v.Hmac = *((*[8]SaiUint32)(unsafe.Pointer(&(s.hmac[0]))))
StructFieldArrFromC = '''v.{0} = *((*{1})(unsafe.Pointer(&(s.{2}[0]))))\n'''  # DstFieldName,DstFieldType SrcFieldArrName
StructToC = r'''
func (v *{0}) C() C.{1} {{{3}
	r := C.{1}{{{2}}}
	return r
}}
'''  # GoType,CType,FieldAssign
StructFromC = r'''
func (v *{0}) fromC(s C.{1}) {{
{2}}}
'''  # GoType,CType,FieldAssign
IdentToC = r'''
func (v *{0}) C() C.{1} {{
	return  C.{1}(*v)
}}
'''  # GoType,CType
IdentFromC = r'''
func (v *{0}) fromC(s C.{1}) {{
	*v = {0}(s)
}}
'''  # GoType,CType
# var si6 gosai.SaiIp6 = *((*gosai.SaiIp6)(unsafe.Pointer(&b[0])))
GoConvTemplate = r'''
func {0}To{1}(v {2}) {1} {{
	var r {1} = *((*{1})(unsafe.Pointer(&v{3})))
	return r
}}
'''  # SrcType,DstType,suffix
UnionInterfaceTemplate = r'''
type {0} interface {{ 
	to{0}() C.{1}
	from{0}(s C.{1})
}}
'''  # GoInterfaceType,CUnionType
UnionCastTemplate = r'''
func (v *{0}) to{1}() C.{2} {{
    vc := (*v){3}
	var r C.{2} = *((*C.{2})(unsafe.Pointer(&vc)))
	return r
}}
'''  # GoType,GoUnionType,CUnionType,FuncCall
UnionCastRevTemplate = r'''
func (v *{0}) from{1}(s C.{2}) {{
	v{4}(*((*C.{3})(unsafe.Pointer(&s))))
}}
'''  # GoType,GoUnionType,CUnionType,CType,FuncCall
saitypes_ast = astperfile['/home/johnnie/MEGA/code/gosai/SAI/inc/saitypes.h']
full_ast = [extdef for extdef in ast.ext if 'saitypes' not in extdef.coord.file and "sai.h" not in extdef.coord.file]
saitypes_ast.extend(full_ast)
typedefs = [d for d in saitypes_ast if type(d) is c_ast.Typedef]
typedecls = [td.type for td in typedefs if type(td.type) is c_ast.TypeDecl]
arrdecls = [td.type for td in typedefs if type(td.type) is c_ast.ArrayDecl]
for arrdecl in arrdecls:
    if type(arrdecl.type) is c_ast.TypeDecl:
        if len(arrdecl.type.quals) != 0:
            print("Error: quals of arrDecl {} is not empty".format(arrdecl.type.declname))
        arrdecl.type.quals = [arrdecl.dim]
        typedecls.insert(0, arrdecl.type)
    else:
        print("Error: arrDecl {} type is not TypeDecl".format(arrdecl))

# typedecltypes = [ type(td.type) for td in typedecls ]
typedecltypes = {"Ident": [], "Union": [], "Enum": [], "Struct": []}
typeslist = {"Ident": [], "Union": [], "Enum": [], "Struct": [], "Primitive": []}


def isIdent(v): return v in typeslist["Ident"]


def isUnion(v): return v in typeslist["Union"]


def isEnum(v): return v in typeslist["Enum"]


def isStruct(v): return v in typeslist["Struct"]


def isPrimitive(v): return v in typeslist["Primitive"]


def isIdentorEnum(v): return isIdent(v) or isEnum(v) or isPrimitive(v)


def typeFuncCall(t):
    if isEnum(t):
        return ""
    if isUnion(t):
        return ".to" + ctomixedcase(t) + "()"
    if isStruct(t) or isIdent(t):
        return ".C()"
    return ""


def fromFuncVal(t, fromval=""):
    if isEnum(t):
        return ""
    if isUnion(t):
        return ".from" + ctomixedcase(t) + "({0})".format(fromval)
    if isStruct(t) or isIdent(t):
        return ".fromC({0})".format(fromval)
    return ""


def fromFunc(t):
    if isEnum(t):
        return " = "
    if isUnion(t):
        return ".from" + ctomixedcase(t)
    if isStruct(t) or isIdent(t):
        return ".fromC"
    if isPrimitive(t):
        return " = "
    return ""


structexcllist = ["sai_fdb_event_notification_data_t"]
typedecls.insert(0,c_ast.TypeDecl("sai_bool_t",[],c_ast.IdentifierType(["bool","bool"])))
unionprimitiveswap = { "bool" : "sai_bool_t"}

for td in typedecls:
    if type(td.type) is c_ast.IdentifierType:
        print("Ident:", td.declname)
        typeslist["Ident"].append(td.declname)
        typeslist["Primitive"].append(td.type.names[0])
        typedict = {"tdtype": "Ident", "ctypename": td.declname}
        typedict["gotypename"] = ctomixedcase(typedict["ctypename"])
        if len(td.type.names) > 1:
            typedict["ctypename"] = td.type.names[1]
        typedict["godecl"] = "\ntype " + typedict["gotypename"] + "  C." + typedict["ctypename"] + "\n"
        typedict["go.C"] = IdentToC.format(typedict["gotypename"], typedict["ctypename"])
        typedict["gofromC"] = IdentFromC.format(typedict["gotypename"], typedict["ctypename"])
        if (len(td.quals) > 0):
            typedict["gocode"] = GoConvTemplate.format("ByteSlice", typedict["gotypename"], "[]byte", "[0]")
        typedecltypes["Ident"].append(typedict)
    if type(td.type) is c_ast.Struct:
        print("Struct:", td.declname)
        if "api" in td.declname:
            continue
        if td.declname in structexcllist:
            continue
        typeslist["Struct"].append(td.declname)
        typedict = {"tdtype": "Struct", "ctypename": td.declname}
        typedict["gotypename"] = ctomixedcase(typedict["ctypename"])
        typedict["structfields"] = []
        for decl in td.type.decls:
            print("structfield:", decl.name)

            if type(decl.type) is c_ast.PtrDecl:
                typedict["listCElem"] = decl.type.type.type.names[0]
                typedict["listGoElem"] = ctomixedcase(typedict["listCElem"])
                typedict["structfields"].append(["*", decl.type.type.type.names[0], decl.name, ctomixedcase(decl.name)])
            if type(decl.type) is c_ast.TypeDecl:
                fieldCtypename = decl.type.type.names[0]
                if decl.name == "type":
                    decl.name = "_type"
                typedict["structfields"].append([fieldCtypename, ctomixedcase(fieldCtypename),
                                                 decl.name, ctomixedcase(decl.name)])
            if type(decl.type) is c_ast.ArrayDecl:
                print("structfieldsArr", decl.name)
                fieldCtypename = decl.type.type.type.names[0]
                typedict["structfields"].append(
                    ["arr", decl.type.dim.value, fieldCtypename, ctomixedcase(fieldCtypename),
                     decl.name, ctomixedcase(decl.name)])

        if "listCElem" in typedict:
            typefunccall = typeFuncCall(typedict["listCElem"])
            typedict["godecl"] = "type {0} []{1}\n".format(typedict["gotypename"], typedict["listGoElem"])
            typedict["go.C"] = listStructToC.format(typedict["gotypename"], typedict["ctypename"],
                                                    typedict["listCElem"], typefunccall)
            fromfunc = fromFunc(typedict["listCElem"])
            typedict["gofromC"] = listStructFromC.format(typedict["gotypename"], typedict["ctypename"],
                                                         typedict["listCElem"], typedict["listGoElem"], fromfunc)
        else:
            structdeclfields = ""
            structToCfields = ""
            structFromCfields = ""
            structToCfieldsConv = ""
            for f in typedict["structfields"]:
                if f[0] == "*":
                    print("Error got pointer field in normal struct:", f)
                    break
                    # return
                if f[0] == "arr":
                    typefunccall = typeFuncCall(f[2])
                    structdeclfields += StructFieldTemplate.format(f[-1], "[" + f[1] + "]" + f[3])
                    structToCfieldsConv += StructFieldArrAssignConv.format(f[-1], "[" + f[1] + "]" + "C." + f[2], f[-1])
                    structToCfields += StructFieldArrAssign.format(f[-2], f[-1])
                    structFromCfields += StructFieldArrFromC.format(f[-1], "[" + f[1] + "]" + f[3], f[-2])
                else:
                    typefunccall = typeFuncCall(f[0])
                    structdeclfields += StructFieldTemplate.format(f[-1], f[1])
                    structToCfields += StructFieldAssign.format(f[-2], f[-1], typefunccall)
                    fromfunc = fromFunc(f[0])
                    # DstFieldName,DstFieldFromFunc,SrcFieldName
                    structFromCfields += StructFieldFromC.format(f[-1], fromfunc, f[-2])
            typedict["godecl"] = StructTemplate.format(typedict["gotypename"], structdeclfields)

            typedict["go.C"] = StructToC.format(typedict["gotypename"], typedict["ctypename"], structToCfields[:-1],
                                                structToCfieldsConv)
            typedict["gofromC"] = StructFromC.format(typedict["gotypename"], typedict["ctypename"], structFromCfields,
                                                     structToCfieldsConv)

            print(typedict)

        typedecltypes["Struct"].append(typedict)
    if type(td.type) is c_ast.Union:
        print("Union:", td.declname)
        typeslist["Union"].append(td.declname)
        typedict = {"tdtype": "Union", "ctypename": td.declname}
        typedict["gotypename"] = ctomixedcase(typedict["ctypename"])
        typedict["godecl"] = UnionInterfaceTemplate.format(typedict["gotypename"], typedict["ctypename"])
        typedict["uniontypes"] = []
        for decl in td.type.decls:
            if type(decl.type) is c_ast.TypeDecl:
                typedict["uniontypes"].append(decl.type.type.names[0])
            if type(decl.type) is c_ast.ArrayDecl:
                print("Ignoring Array type:", decl.name)
        for ut in typedict["uniontypes"]:
            # gouniontype = ctomixedcase(t)
            t = ut
            if not (isIdent(t) or isStruct(t) or isUnion(t) or isEnum(t) or isPrimitive(t)):
                print("Error: {} not found".format(t))
            if isPrimitive(t) and t in unionprimitiveswap:
                print("Swap primitive", t,"to",unionprimitiveswap[t])
                t = unionprimitiveswap[ut]
            if isUnion(t):
                print("Error:UnionInUnion", t)
            if isEnum(t):
                print("Error:EnumInUnion", t)
            if isStruct(t):
                findstruct = [structdict for structdict in typedecltypes["Struct"] if t in structdict["ctypename"]]
                if len(findstruct) != 1:
                    print("Error: found incorrect number of structdict entries for {}:{} expected 1".format(t, len(
                        findstruct)))
                structdict = findstruct[0]
                if not "gounion" in structdict: structdict["gounion"] = ""
                unioncastfunc = UnionCastTemplate.format(structdict["gotypename"], typedict["gotypename"],
                                                         typedict["ctypename"], ".C()")
                unioncastfromfunc = UnionCastRevTemplate.format(structdict["gotypename"], typedict["gotypename"],
                                                                typedict["ctypename"], structdict["ctypename"],
                                                                ".fromC")
                if unioncastfunc not in structdict["gounion"]:
                    structdict["gounion"] += unioncastfunc
                if unioncastfromfunc not in structdict["gounion"]:
                    structdict["gounion"] += unioncastfromfunc
            if isIdent(t):
                findIdent = [identdict for identdict in typedecltypes["Ident"] if ut in identdict["ctypename"]]
                if len(findIdent) != 1:
                    print("Error: found incorrect number of identict entries for {}:{} expected 1".format(t, len(
                        findIdent)))
                identdict = findIdent[0]
                if not "gounion" in identdict: identdict["gounion"] = ""
                unioncastfunc = UnionCastTemplate.format(identdict["gotypename"], typedict["gotypename"],
                                                         typedict["ctypename"], "")
                unioncastfromfunc = UnionCastRevTemplate.format(identdict["gotypename"], typedict["gotypename"],
                                                                typedict["ctypename"], identdict["ctypename"],
                                                                ".fromC")
                if unioncastfunc not in identdict["gounion"]:
                    identdict["gounion"] += unioncastfunc
                if unioncastfromfunc not in identdict["gounion"]:
                    identdict["gounion"] += unioncastfromfunc

        typedecltypes["Union"].append(typedict)
    if type(td.type) is c_ast.Enum:
        print("Enum:", td.declname)
        typeslist["Enum"].append(td.declname)
        typedict = {"tdtype": "Enum", "ctypename": td.declname}
        typedict["enumnames"] = [ n.name for n in td.type.values]
        typedict["godecl"] = "const (\n"
        for enumname in typedict["enumnames"]:
            typedict["godecl"] += "\t{0}\t= C.{1}\n".format(ctomixedcase(enumname.lower(),replace=""),enumname)
        typedict["godecl"] += ")\n"
        # typedict["gotypename"] = ctomixedcase(typedict["ctypename"])
        typedecltypes["Enum"].append(typedict)
fulltypes = []
fulltypes.extend(typedecltypes["Ident"])
fulltypes.extend(typedecltypes["Union"])
fulltypes.extend(typedecltypes["Struct"])
fulltypes.extend(typedecltypes["Enum"])

outtxt = r'''package gosai
// #cgo CFLAGS: -I ../../../SAI/inc -I../../ -I../gen-inc
// #cgo LDFLAGS: -L${SRCDIR}/../cmake-build-debug -ladaptor
// #cgo LDFLAGS: -L/home/johnnie/MEGA/code/gosai/lib/x86_64-linux-gnu -lsai -Wl,-unresolved-symbols=ignore-in-shared-libs
/*
#include "sai_adaptor.h" 
*/
import "C"
import (
	"unsafe"
)

'''
for t in fulltypes:
    for outsection in ["godecl", "gocode", "go.C", "gofromC", "gounion"]:
        if outsection in t:
            outtxt += t[outsection]
# print(outtxt)
with open("adaptor/gosai/saitypes.go", 'w') as f:
    f.write(outtxt)
# print(saitypes_ast)
print(saitypes_ast == typedefs)
print(typedefs == typedecls)
print(typedecltypes)

# sai_status_t sai_create_acl_table(sai_object_id_t *acl_table_id, sai_object_id_t switch_id, uint32_t attr_count, const sai_attribute_t *attr_list);
CreateNoSwitchIdFuncTemplate = r'''
func {0}({2} attrlist SaiAttributeList) (SaiObjectId,SaiStatus) {{
	retOdjId := new(C.sai_object_id_t)
	count, list := attrlist.C()
	retstatus := C.{1}(retOdjId{3},count,list)
	return SaiObjectId(*retOdjId),SaiStatus(retstatus)
}}
'''  # GoFuncName,CFuncName
CreateFuncTemplate = CreateNoSwitchIdFuncTemplate.replace("{{","{{{{").replace("}}","}}}}").format("{0}","{1}","switchId SaiObjectId,",",switchId.C()")
# sai_status_t sai_remove_acl_table(sai_object_id_t acl_table_id);
RemoveFuncTemplate = r'''
func {0}(objId SaiObjectId) SaiStatus {{
	retstatus := C.{1}(objId.C())
	return SaiStatus(retstatus)
}}
'''  # GoFuncName,CFuncName
# sai_status_t sai_set_acl_table_attribute(sai_object_id_t acl_table_id, const sai_attribute_t *attr);
SetFuncTemplate = r'''
func {0}(objId SaiObjectId, attr SaiAttribute) SaiStatus {{
	attrC := attr.C()
	retstatus := C.{1}(objId.C(),&attrC)
	return SaiStatus(retstatus)
}}
'''  # GoFuncName,CFuncName
# sai_status_t sai_get_acl_table_attribute(sai_object_id_t acl_table_id, uint32_t attr_count, sai_attribute_t *attr_list
GetFuncTemplate = r'''
func {0}(objId SaiObjectId, attrlist *SaiAttributeList) (SaiStatus) {{
	count, list := attrlist.C()
	retstatus := C.{1}(objId.C(),count,list)
	attrlist.fromC(count, list)
	return SaiStatus(retstatus)
}}
'''  # GoFuncName,CFuncName
# sai_status_t sai_get_bridge_port_stats(sai_object_id_t bridge_port_id, uint32_t number_of_counters,
#                                                               const sai_stat_id_t *counter_ids, uint64_t *counters)
GetStatsFuncTemplate = r'''
func {0}(objId SaiObjectId, counterIds []SaiStatId{3}) ([]uint64,SaiStatus) {{{2}
	RetCounters := make([]uint64,count)
	pcRetCounters := (*C.uint64_t)(unsafe.Pointer(&RetCounters[0]))
	retStatus := C.{1}(objId.C(),C.uint32_t(count),pcStatIds{4},pcRetCounters)
	return RetCounters,SaiStatus(retStatus)
}}
'''  # GoFuncName,CFuncName,StatIdsArrTemplate,GoFuncParam,CFuncParam
StatIdsArrTemplate = r'''
	count := len(counterIds)
	cStatIds := make([]C.sai_stat_id_t,count)
	for i, val := range counterIds {
		cStatIds[i] = C.sai_stat_id_t(val.C())
	}
	pcStatIds := (*C.sai_stat_id_t)(unsafe.Pointer(&cStatIds[0]))
''' # none
# sai_status_t sai_clear_bridge_port_stats(sai_object_id_t bridge_port_id, uint32_t number_of_counters, const sai_stat_id_t *counter_ids)
ClearStatsFuncTemplate = r'''
func {0}(objId SaiObjectId, counterIds []SaiStatId) SaiStatus {{{2}
	retStatus := C.{1}(objId.C(),C.uint32_t(count),pcStatIds)
	return SaiStatus(retStatus)
}}
'''  # GoFuncName,CFuncName,StatIdsArrTemplate
# sai_status_t sai_create_fdb_entry(const sai_fdb_entry_t *fdb_entry, uint32_t attr_count, const sai_attribute_t *attr_list)
CreateNonObjFuncTemplate = r'''
func {0}(param0 {2}, attrlist SaiAttributeList) SaiStatus {{
	cparam0 := param0.C()
	count, list := attrlist.C()
	retstatus := C.{1}(&cparam0,count,list)
	return SaiStatus(retstatus)
}}
'''  # GoFuncName,CFuncName,param0GoType
# sai_status_t sai_remove_fdb_entry(const sai_fdb_entry_t *fdb_entry)
RemoveNonObjFuncTemplate = r'''
func {0}(param0 {2}) SaiStatus {{
	cparam0 := param0.C()
	retstatus := C.{1}(&cparam0)
	return SaiStatus(retstatus)
}}
'''  # GoFuncName,CFuncName,param0GoType
# sai_status_t sai_set_fdb_entry_attribute(const sai_fdb_entry_t *fdb_entry, const sai_attribute_t *attr)
SetNonObjFuncTemplate = r'''
func {0}(param0 {2}, attr SaiAttribute) SaiStatus {{
	cparam0 := param0.C()
	attrC := attr.C()
	retstatus := C.{1}(&cparam0,&attrC)
	return SaiStatus(retstatus)
}}
'''  # GoFuncName,CFuncName,param0GoType
# sai_status_t sai_get_fdb_entry_attribute(const sai_fdb_entry_t *fdb_entry, uint32_t attr_count, sai_attribute_t *attr_list)
GetNonObjFuncTemplate = r'''
func {0}(param0 {2}, attrlist *SaiAttributeList) (SaiStatus) {{
	cparam0 := param0.C()
	count, list := attrlist.C()
	retstatus := C.{1}(&cparam0,count,list)
	attrlist.fromC(count, list)
	return SaiStatus(retstatus)
}}
'''  # GoFuncName,CFuncName,param0GoType
FuncFile = r'''package gosai
// #cgo CFLAGS: -I ../../../SAI/inc -I../../ -I../gen-inc
// #cgo LDFLAGS: -L${SRCDIR}/../cmake-build-debug -ladaptor
// #cgo LDFLAGS: -L/home/johnnie/MEGA/code/gosai/lib/x86_64-linux-gnu -lsai -Wl,-unresolved-symbols=ignore-in-shared-libs
/*
#include "sai_adaptor.h" 
*/
import "C"
import (
	"unsafe"
)

type SaiAttributeList []SaiAttribute

func (v SaiAttributeList) C() (C.uint32_t,*C.sai_attribute_t)  {
    cv := make([]C.sai_attribute_t,len(v))
    for i, val := range v {
        cv[i] = C.sai_attribute_t(val.C())
    }
	return C.uint32_t(len(v)),(*C.sai_attribute_t)(unsafe.Pointer(&cv[0]))
}
func (v *SaiAttributeList) fromC(count C.uint32_t,list *C.sai_attribute_t) {
	clen := int(count)
	vlen := len(*v)
	if vlen < clen {
		nv := make(SaiAttributeList,clen,clen)
		copy(nv,*v)
		*v = nv
	}
	cslice := (*[1 << 28]C.sai_attribute_t)(unsafe.Pointer(list))[:clen:clen]
	for i, val := range cslice {
		(*v)[i].fromC(val)
	}
}
'''
# funcexcllist = [ "ipmc_entry", "l2mc_entry", "inseg_entry", "neighbor_entry", "route_entry", "switch","sai_clear_port_all_stats","sai_get_tam_snapshot_stats"]
funcexcllist = ["sai_clear_port_all_stats","sai_get_tam_snapshot_stats"]
for decl in c_func_adaptor_defs:
    if type(decl.type.args.params[0].type) is c_ast.PtrDecl:
        param0type = decl.type.args.params[0].type.type.type.names[0]
    else:
        param0type = decl.type.args.params[0].type.type.names[0]
    if any(excl in decl.name for excl in funcexcllist):
        print("Skipping:", decl.name, param0type)
        continue
    prevFuncFile = FuncFile
    if param0type == "sai_object_id_t":
        if "sai_create" in decl.name:
            if "sai_create_switch" == decl.name:
                FuncFile += CreateNoSwitchIdFuncTemplate.format(ctomixedcase(decl.name), decl.name,"","")
            else:
                FuncFile += CreateFuncTemplate.format(ctomixedcase(decl.name), decl.name)
        if "sai_remove" in decl.name:
            FuncFile += RemoveFuncTemplate.format(ctomixedcase(decl.name), decl.name)
        if "sai_set" in decl.name:
            FuncFile += SetFuncTemplate.format(ctomixedcase(decl.name), decl.name)
        if "sai_get" in decl.name and "stats" not in decl.name:
            FuncFile += GetFuncTemplate.format(ctomixedcase(decl.name), decl.name)
        if "sai_get" in decl.name and "stats" == decl.name[-5:]:
            FuncFile += GetStatsFuncTemplate.format(ctomixedcase(decl.name), decl.name,StatIdsArrTemplate,"","")
        if "sai_get" in decl.name and "stats_ext" == decl.name[-9:]:
            FuncFile += GetStatsFuncTemplate.format(ctomixedcase(decl.name), decl.name,StatIdsArrTemplate,
                                                                                ", mode uint",", C.sai_stats_mode_t(mode)")
        if "sai_clear" in decl.name:
            FuncFile += ClearStatsFuncTemplate.format(ctomixedcase(decl.name), decl.name,StatIdsArrTemplate)
    if param0type[-7:] == "entry_t":
        if "sai_create" in decl.name:
            FuncFile += CreateNonObjFuncTemplate.format(ctomixedcase(decl.name), decl.name,ctomixedcase(param0type))
        if "sai_remove" in decl.name:
            FuncFile += RemoveNonObjFuncTemplate.format(ctomixedcase(decl.name), decl.name,ctomixedcase(param0type))
        if "sai_set" in decl.name:
            FuncFile += SetNonObjFuncTemplate.format(ctomixedcase(decl.name), decl.name,ctomixedcase(param0type))
        if "sai_get" in decl.name:
            FuncFile += GetNonObjFuncTemplate.format(ctomixedcase(decl.name), decl.name,ctomixedcase(param0type))

    if FuncFile == prevFuncFile:
        print("noAction:",decl.name)

with open("adaptor/gosai/saifuncs.go", 'w') as f:
    f.write(FuncFile)
# ast.show()
v = AdaptorVisitor()
# v.visit(ast)
