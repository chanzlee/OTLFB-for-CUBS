from Crypto.Cipher import DES3


def decrip(key,input):

    if len(input) != 8:
        return input

    #create new encryption cipher
    des = DES3.new(key, DES3.MODE_ECB)
    weight = []

    #assign each digit a weight]
    weight.append(des.encrypt('00000000'.encode("utf8"))+b'0')
    weight.append(des.encrypt('00000001'.encode("utf8"))+b'1')
    weight.append(des.encrypt('00000002'.encode("utf8"))+b'2')
    weight.append(des.encrypt('00000003'.encode("utf8"))+b'3')
    weight.append(des.encrypt('00000004'.encode("utf8"))+b'4')
    weight.append(des.encrypt('00000005'.encode("utf8"))+b'5')
    weight.append(des.encrypt('00000006'.encode("utf8"))+b'6')
    weight.append(des.encrypt('00000007'.encode("utf8"))+b'7')
    weight.append(des.encrypt('00000008'.encode("utf8"))+b'8')
    weight.append(des.encrypt('00000009'.encode("utf8"))+b'9')
    weight.sort()#sort, creating a new cipher
    midput = []
    output = []
    #shift digits based on new cipher


    for ch in input:
        i = 0
        for w in weight:
            if ch == str(w)[-2]:
                midput.append(str(i))
            i += 1
    midput = ''.join(midput)
    if int(midput[5:8]) > 122:
        letter = chr(int(midput[5:7]))
    else:
        letter = chr(int(midput[5:8]))
    output = midput[0:5] + letter
    return(output)


def encrip(key,input):
    #create new encryption cipher
    des = DES3.new(key, DES3.MODE_ECB)
    weight = []

    #assign each digit a weight]
    weight.append(des.encrypt('00000000'.encode("utf8"))+b'0')
    weight.append(des.encrypt('00000001'.encode("utf8"))+b'1')
    weight.append(des.encrypt('00000002'.encode("utf8"))+b'2')
    weight.append(des.encrypt('00000003'.encode("utf8"))+b'3')
    weight.append(des.encrypt('00000004'.encode("utf8"))+b'4')
    weight.append(des.encrypt('00000005'.encode("utf8"))+b'5')
    weight.append(des.encrypt('00000006'.encode("utf8"))+b'6')
    weight.append(des.encrypt('00000007'.encode("utf8"))+b'7')
    weight.append(des.encrypt('00000008'.encode("utf8"))+b'8')
    weight.append(des.encrypt('00000009'.encode("utf8"))+b'9')
    weight.sort()#sort, creating a new cipher
    midput = []
    output = []
    #shift digits based on new cipher
    for ch in input:
        if ch.isalpha():
            midput.append(str(ord(ch.lower())))
        else:
            midput.append(str(ch))
    midput = ''.join(midput)
    for n in midput:
        output.append(str(weight[int(n)])[-2])
    output = ''.join(output)
    output = output[::-1].zfill(8)[::-1]
    return(output)

