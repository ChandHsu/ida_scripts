# -*- coding: utf-8 -*-

class RegX:
    def __init__(self, num):
        self.available = False
        self.num = num
        self.value = 0

    def writeX(self, value):
        self.available = True
        self.value = value

    def getX(self):
        return self.value

def handle_adrp(addr):
    page = GetOperandValue(addr, 1)
    reg = GetOpnd(addr, 0)
    store_reg(reg, page)

def handle_add(addr):
    dstReg = GetOpnd(addr, 0)
    op1 = GetOpnd(addr, 1)
    op2 = GetOpnd(addr, 2)
    result = get_operand_value(addr, op1, 1)
    result += get_operand_value(addr, op2, 2)
    store_reg(dstReg, result)

def handle_ldrb(addr):
    dstRegOp = GetOpnd(addr, 0)
    srcOp = GetOpnd(addr, 1)
    srcAddr, _ = get_operand_indirect_addr(srcOp)
    store_reg(dstRegOp, Byte(srcAddr))

def handle_strb(addr):
    srcRegOp = GetOpnd(addr, 0)
    dstOp = GetOpnd(addr, 1)
    dstAddr, isStatic = get_operand_indirect_addr(dstOp)
    value = get_operand_value(addr, srcRegOp, 0)
    if isStatic:
        print('================> == ┬─┬ ノ( ゜-゜ノ) patch addr {} with byte {}'.format(hex(dstAddr), value))
        idc.PatchByte(dstAddr, value)
    else:
        raise Exception('unsupport STRB to heap')

def handle_mov(addr):
    dstRegOp = GetOpnd(addr, 0)
    src = GetOpnd(addr, 1)
    srcValue = get_operand_value(addr, src, 1)
    store_reg(dstRegOp, srcValue)

def handle_eor(addr):
    dstRegOp = GetOpnd(addr, 0)
    op1 = GetOpnd(addr, 1)
    op2 = GetOpnd(addr, 2)
    val1 = get_operand_value(addr, op1, 1)
    val2 = get_operand_value(addr, op2, 2)
    val = val1 ^ val2
    store_reg(dstRegOp, val)
    print('[+] ================> (╯°□°）╯︵ ┻━┻ decrypted eor value ' + str(val) + ', ' + chr(val))

def handle_and(addr):
    dstRegOp = GetOpnd(addr, 0)
    op1 = GetOpnd(addr, 1)
    op2 = GetOpnd(addr, 2)
    val1 = get_operand_value(addr, op1, 1)
    val2 = get_operand_value(addr, op2, 2)
    val = val1 & val2
    store_reg(dstRegOp, val) 

def handle_stur(addr):
    srcRegOp = GetOpnd(addr, 0)
    dstOp = GetOpnd(addr, 1)
    dstAddr, isStatic = get_operand_indirect_addr(dstOp)
    value = get_operand_value(addr, srcRegOp, 0)
    if not isStatic:
        memory[dstAddr] = value
        print('[+] store {} in memory[{}]'.format(value, dstAddr))
    else:
        raise Exception('unspport STUR to static memory')

def handle_ldur(addr):
    dstRegOp = GetOpnd(addr, 0)
    srcOp = GetOpnd(addr, 1)
    srcAddr, isStatic = get_operand_indirect_addr(srcOp)
    if isStatic:
        value = Byte(srcAddr)
    else:
        value = memory[srcAddr]
        print('[+] retrieve {} from memory[{}]'.format(value, srcAddr))
    store_reg(dstRegOp, value)

def get_operand_value(addr, operand, num):
    if operand.startswith('X') or operand.startswith('W'):
        reg = x[int(operand[1:])]
        if reg.available:
            return reg.getX()
        else:
            print('[-] invalid reg state ' + operand)
            raise Exception('[-] invalid reg state ' + operand)
    elif operand.startswith('#'):
        return GetOperandValue(addr, num)
    raise Exception('unresolved operand ' + operand)

def get_operand_indirect_addr(operand):
    if not operand.startswith('[') or not operand.endswith(']'):
        raise Exception('invalid operand for indirect addr calculate ' + operand)
    operand = operand[1:-1]
    if operand.startswith('X') or operand.startswith('W'):
        reg = None
        imm = 0
        if ',' in operand:
            parts = operand.split(',')
            reg = x[int(parts[0][1:])]
            immPart = parts[1][1:]

            if '(' in immPart:
                immPart = immPart[1:-1]
                if '-' in immPart:
                    binop = '-'
                elif '+' in immPart:
                    binop = '+'
                else:
                    raise Exception('unresolved operand ' + operand)

                imms = immPart.split(binop)
                imm0_expr = imms[0].strip()
                imm1_expr = imms[1].strip()
                imm0 = get_imm_value(imm0_expr)
                imm1 = get_imm_value(imm1_expr)
                imm = imm0 + imm1 if binop == '+' else imm0 - imm1
            else:
                imm = get_imm_value(immPart)
        else:
            reg = x[int(operand[1:])]
    else:
        raise Exception('unresolved operand ' + operand)

    # FIXME: very dirty hack
    if reg.num == 29:
        isStatic = False
    else:
        isStatic = True
    addr = reg.getX() + imm
    print('[+] calculate indirect addr for operand {}, value {}'.format(operand, hex(addr)))
    return addr, isStatic

def get_imm_value(imm_expr):
    if '_' in imm_expr:
        return int('0x' + imm_expr.split('_')[1], 0)
    return int(imm_expr, 0)

def store_reg(regOp, value):
    if regOp.startswith('X') or regOp.startswith('W'):
        reg = x[int(regOp[1:])]
        reg.writeX(value)
        print('[+] store {} in {}'.format(value, regOp))
    else:
        raise Exception('unresolved reg ' + dstReg)

x = [None] * 31
for i in range(31):
    x[i] = RegX(i)

x[29].writeX(0)

handlers = {
    'ADRP': handle_adrp,
    'ADD': handle_add,
    'LDRB': handle_ldrb,
    'STRB': handle_strb,
    'MOV': handle_mov,
    'EOR': handle_eor,
    'AND': handle_and,
    'STUR': handle_stur,
    'LDUR': handle_ldur
}

# simulator memory
memory = {}

def u0_xorpath(startAddr, endAddr):
    if endAddr < startAddr:
        raise Exception('invalid input params')
    print('xorpath from {} to {}'.format(hex(startAddr), hex(endAddr)))
    cursor = startAddr
    for _ in range(1 + (endAddr - startAddr) // 4):
        mnem = GetMnem(cursor)
        print('[*] {} {}'.format(hex(cursor), GetDisasm(cursor)))
        if mnem in handlers:
            handlers[mnem](cursor)
        else:
            print('[-] Warn: unresolved mnem ' + mnem + ' at ' + str(hex(cursor)))
            raise Exception('unresolved mnem ' + mnem + ' at ' + str(hex(cursor)))
        cursor += 4

if __name__ == '__main__':
    u0_xorpath(0x10007A928, 0x10007BC7C)