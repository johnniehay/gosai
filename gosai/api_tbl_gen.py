from pycparser import c_parser, c_ast, parse_file,c_generator
def generate_sai_api_tbl_h(apis):
    def createDecl(api):
        apitype = 'sai_'+api+'_api_t'
        apivar =  'sai_'+api+'_api_tbl'
        return c_ast.Decl(apivar, list(), list(),list(),
                          c_ast.PtrDecl(list(),
                                        c_ast.TypeDecl(apivar, list(),
                                                       c_ast.IdentifierType([apitype,]))),None,None)

    tdecls = [createDecl(api) for api in apis]
    tstruct = c_ast.Struct('_sai_api_tbl_t',tdecls)
    tdec = c_ast.TypeDecl('sai_api_tbl_t',list(),tstruct)
    tdef = c_ast.Typedef('sai_api_tbl_t', list(), ['typedef'],tdec)
    externdec =c_ast.Decl('sai_api_tbl',list(),['extern'],list(),
                          c_ast.TypeDecl('sai_api_tbl',list(),
                                         c_ast.IdentifierType(['sai_api_tbl_t'])),None,None)
    api_t =c_ast.FileAST([tdef,externdec])
    generator = c_generator.CGenerator()
    sai_api_tbl_h_str = r'''#include "sai.h"
#ifndef SAI_API_TBL
#define SAI_API_TBL

'''
    sai_api_tbl_h_str += generator.visit(api_t)
    sai_api_tbl_h_str += r'''
extern sai_status_t sai_api_tbl_init();

#endif
'''
    # print(api_t)
    print(sai_api_tbl_h_str)
    with open('adaptor/gen-inc/sai_api_tbl.h','w') as f:
        f.write(sai_api_tbl_h_str)
def generate_sai_api_tbl_init_c(apis,api_enum):
    sai_api_tbl_init_str = r'''#include "sai_api_tbl.h"
#include <stdio.h>

sai_api_tbl_t sai_api_tbl = {0};

'''
    for api in apis:
        apitype = 'sai_'+api+'_api_t'
        apivar =  'sai_'+api+'_api_tbl'
        sai_api_tbl_init_str += apitype + " *" + apivar + " = 0;\n"

    sai_api_tbl_init_str += r'''
sai_status_t sai_api_tbl_init()
{
    sai_status_t sai_ret;
    do {
'''
    for api, enum in zip(apis,api_enum):
        sai_api_tbl_init_str += r'''        sai_ret = sai_api_query('''
        sai_api_tbl_init_str += enum
        # sai_api_tbl_init_str += r''', (void *)&(sai_api_tbl.sai_'''
        sai_api_tbl_init_str += r''', (void **)&(sai_'''
        sai_api_tbl_init_str += api
        sai_api_tbl_init_str += r'''_api_tbl));
        sai_api_tbl.sai_'''
        sai_api_tbl_init_str += api
        sai_api_tbl_init_str += r'''_api_tbl = sai_'''
        sai_api_tbl_init_str += api
        sai_api_tbl_init_str += r'''_api_tbl;
        if (sai_ret != SAI_STATUS_SUCCESS) {
            fputs("'''
        sai_api_tbl_init_str += enum
        sai_api_tbl_init_str +=r''' not found\n",stderr);
        }
'''

    sai_api_tbl_init_str += r'''    } while(0);

    return sai_ret;
}
'''
    print(sai_api_tbl_init_str)
    with open('adaptor/gen-src/sai_api_tbl_init.c','w') as f:
        f.write(sai_api_tbl_init_str)

if __name__ == '__main__':
    # generate_sai_api_tbl_h(['switch','mpls'])
    generate_sai_api_tbl_init_c(['switch','mpls'],['SAI_API_SWITCH','SAI_API_MPLS'])
