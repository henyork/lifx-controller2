import socket
import struct
import sys
from machine import Pin, ADC
import time
import network

f = open('test.txt','a')

f.write('hello')

f.close()

#ap = network.WLAN(network.WLAN.IF_AP)
#ap.config(ssid='control', password='lightcontrol', authmode=network.AUTH_WPA_WPA2_PSK)
#ap.active(True)



if sys.implementation.name == 'micropython':
    MP = True
else:
    MP = False
#import network

print("wifi running")

class TimeoutError(Exception):
    pass

f = open('main.txt','a')
f.close()
ap = network.WLAN(network.WLAN.IF_AP)
print('network is :', ap.active())
if not ap.active():
    ap.config(ssid='control', password='lightcontrol', authmode=network.AUTH_WPA_WPA2_PSK)
    ap.active(True)


server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
server_socket.settimeout(0.25)

class Lights():
    


    def __init__(self, server_socket):
        self.server_socket = server_socket
        self.targets = []
        
    def get_responses(self):

        #get response
        responses = []
        exit = False
        while(exit == False):
            try:
                if MP:
                    data = self.server_socket.recv(100)
                else:
                    data = self.server_socket.recv(100)
            except OSError:
                exit = True
            else:
                response_packet = Packet(byte_data=data)
                responses.append(response_packet)
        return responses

    def scan(self):
        #identify lights connected to network
        
        #create GetService packet
        header = {
            'size':36,
            'protocol':1024,
            'addressable':True,
            'tagged':False,
            'origin':0,
            'source':2, #this should be anything other than 0 or 1
            'target':0, #all devices
            'res_required':True,
            'ack_required':True,
            'sequence':1,
            'type': 2
        
        }

        get_service = Packet(header = header)
        
        self.server_socket.sendto(get_service.byte_data, ('192.168.4.255',56700))

        responses = self.get_responses()
        
        for response in responses:
            #add each target light to the list of targets
            if response.header['target'] not in self.targets:
                self.targets.append(response.header['target'])
        print(self.targets)
    
    def set_color(self, hue, saturation, brightness, kelvin, duration = 0, index = None):
        if index is None or len(self.targets) < 1:
            target = 0
        else:
            target = self.targets[index]
        header = {
            'size':49,
            'protocol':1024,
            'addressable':True,
            'tagged':True,
            'origin':0,
            'source':2, #this should be anything other than 0 or 1
            'target':target, #all devices
            'res_required':False,
            'ack_required':False,
            'sequence':1,
            'type': 102
        
        }
        payload = {
            'hue' : hue,
            'saturation' : saturation,
            'brightness' : brightness,
            'kelvin' : kelvin,
            'duration' : duration
        }
        set_color_packet = Packet(header=header, payload=payload)
        self.server_socket.sendto(set_color_packet.byte_data, ('192.168.4.255',56700))
        #responses = self.get_responses()
        #for response in responses:
        #    for key in response.header:
        #            print(f'{key} = {response.header[key]}')
        #    for key in response.payload:
        #        print(f'{key} = {response.payload[key]}')

class Packet():


    def __init__(self, byte_data = None, header = None, payload=None):
        
        if byte_data is not None and header is not None or (byte_data is None and header is None):
            raise ValueError('Either byte_data or header are required as arguments')
        
        if byte_data is not None and type(byte_data) != bytes:
            raise ValueError('byte_data must be a bytes object or none')
    
        if header is not None and type(header) != dict:
            raise ValueError('header must be a dictionary or none')
        
        if payload is not None and type(payload) != dict:
            raise ValueError('payload must be a dictionary or none')


        if byte_data is not None:
            self.header, self.payload = self.from_byte_data(byte_data)
            
        if header is not None:
            self.byte_data = self.from_dict(header, payload)
            
        
    def from_byte_data(self, byte_data):
        byte_data = bytearray(byte_data)
        
        header_data = struct.unpack('<hBBiq3hBBqhh', byte_data[0:36])

        header = {

            'size':header_data[0],
            'protocol':1024,
            'addressable':header_data[2]>>4,
            'tagged':header_data[2]>>5,
            'origin':0,
            'source':header_data[3],
            'target':header_data[4]>>2, #all devices
            'res_required':header_data[8] & 0b00000001,
            'ack_required':header_data[8] & 0b00000010 >> 1,
            'sequence':header_data[9],
            'type': header_data[11]
            
        }
        payload = {}

        payload_size = 36 - header['size']

        if header['type'] == 3: #StateService packet
            payload['service'], payload['port'] = struct.unpack('<bi', byte_data[36:41])
        if header['type'] == 22:
            payload['level'] = struct.unpack('<H',byte_data[36:38])[0]
        if header['type'] == 107:
            print('LightState packet received')
            payload['hue'], payload['saturation'], payload['brightness'], payload['kelvin'], reserved, payload['power'], payload['label'], reserved = struct.unpack('<HHHHHH32sQ',byte_data[36:header['size']])
        return header, payload


    def from_dict(self, header, payload):
        byte_2 = 0
        byte_3 = 0b00000100 | header['addressable'] << 4 | header['tagged'] << 5
        byte_22 = header['res_required'] | header['ack_required'] << 1
        
        #f-spec : python type, num byte_data
        #h : integer, 2
        #i : integer, 4
        #b : integer, 1
        #q : integer, 8
        byte_data = bytearray()

        #pack the header
        frame_header = struct.pack('<hBBi', header['size'], byte_2, byte_3, header['source'])
        frame_address = struct.pack('<q3hBB',0, 0, 0, 0, byte_22, header['sequence'])         
        protocol_header = struct.pack('qhh',0 , header['type'],0)

        byte_data.extend(frame_header)
        byte_data.extend(frame_address)
        byte_data.extend(protocol_header)

        #now pack the payload
        
        if header['type'] == 21:
            #SetPower packet
            payload_data = struct.pack('<H',payload['level'])
            byte_data.extend(payload_data)
        if header['type'] == 102:
            #SetColor packet
            payload_data = struct.pack('<BHHHHI',0,payload['hue'],payload['saturation'],payload['brightness'],payload['kelvin'],payload['duration'])
            byte_data.extend(payload_data)
            print('payload len:',len(payload_data))
            print('payload',payload_data)
            
        
        #for i, byte in enumerate(byte_data):
        #    print(f'#{i} = {byte}')
        return byte_data
    
    

        

            
header = {
    'size':38,
    'protocol':1024,
    'addressable':True,
    'tagged':True,
    'origin':0,
    'source':2, #this should be anything other than 0 or 1
    'target':0, #all devices
    'res_required':True,
    'ack_required':True,
    'sequence':1,
    'type': 21
    
}

on_payload = {
    'level':1
}

off_payload = {
    'level':0
}


on = Pin(32, Pin.IN, Pin.PULL_UP)
off = Pin(33, Pin.IN, Pin.PULL_UP)

v_in = ADC(36, atten=ADC.ATTN_11DB)
a_in = ADC(39, atten=ADC.ATTN_11DB)
s_in = ADC(34, atten=ADC.ATTN_11DB)
h_in = ADC(35, atten=ADC.ATTN_11DB)

last_time = time.time()

while(len(ap.status('stations')) < 1):
    print('waiting for light to connect')

    time.sleep(0.75)

print('light connected to wifi. scanning..')
lights = Lights(server_socket)
lights.scan()
color = [65355, 65355, 65355]
lights.set_color(color[0],color[1], color[2], 65355, 0)
color_change = False
while(True):

    #print('adc1', r_in.read_uv())
    #print(time.time())

    if time.time() - last_time > 2:
        print('network status:', ap.status('stations'))
        last_time = time.time()

    if h_in.read_uv() > 2500000:
        color[0] += 500
        color_change = True
    if h_in.read_uv() < 500000:
        color[0] -= 500
        color_change = True
    if s_in.read_uv() > 2500000:
        color[1] += 2000
        color_change = True
    if s_in.read_uv() < 500000:
        color[1] -= 2000
        color_change = True
    if v_in.read_uv() > 2500000:
        color[2] += 2000
        color_change = True
    if v_in.read_uv() < 500000:
        color[2] -= 2000
        color_change = True
    print('color=',color[0],color[1],color[2])
    for i, val in enumerate(color):
        
        if val > 65535:
            color[i] = 65535
        if val < 0:
            color[i] = 0

    if color_change:
        lights.set_color(color[0],color[1], color[2], 65355, 0)
        color_change = False

    
    


    if on.value() == 0:
        print('sending on packet')
        #packet = Packet(header = header, payload=on_payload)
        #server_socket.sendto(packet.byte_data, ('192.168.4.255',56700))
        lights.set_color(20000,65355, 65355, 65355, 5000)
        
        while(on.value() == 0):
            time.sleep(0.05)

    if off.value() == 0:
        print('sending off packet')
        lights.set_color(-1, 10000,65355, 65355, 5000, 10)
        #server_socket.sendto(packet.byte_data, ('192.168.4.255',56700))
        exit = False
        while(exit == False):
            try:
                if MP:
                    data = server_socket.read()
                else:
                    data = server_socket.recv(100)
            except OSError:
                exit = True
            else:
                response_packet = Packet(byte_data=data)
                print('\nGot response packet:')
                for key in response_packet.header:
                    print(f'{key} = {response_packet.header[key]}')
                for key in response_packet.payload:
                    print(f'{key} = {response_packet.payload[key]}')
        while(off.value() == 0):
            time.sleep(0.05)
    time.sleep(0.05)
      
    

    




