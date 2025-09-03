import socket
import struct
print('running')
#socket.AF_INET
#server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#server_socket.bind(('', 56700))


class Packet():


    def __init__(self, header):
        
        


        byte_3 = 1024 + 0b00100000
        
        if header['tagged']:
            byte_3 += 0b00100000
        print(byte_3)

        bytes = struct.pack('<hhil',header['size'],byte_3,header['source'],header['target'])
        print(bytes)




header = {
    'size':1,
    'protocol':1024,
    'addressable':True,
    'tagged':True,
    'origin':0,
    'source':2,
    'target':0, #all devices
    'reserved':0,
    'res_required':False,
    'ack_required':True,
    'reserved':0,
    'sequence':1,
    'reserved':0,
    'pkt_type':102,
    'reserved':0
}

packet = []


packet = Packet(header)


