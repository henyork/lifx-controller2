import network

f = open('test.txt','a')

f.write('hello')

f.close()

ap = network.WLAN(network.WLAN.IF_AP)
ap.config(ssid='control', password='lightcontrol', authmode=network.AUTH_WPA_WPA2_PSK)
ap.active(True)

