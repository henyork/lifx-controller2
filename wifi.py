import network

print("wifi running")

ap = network.WLAN(network.WLAN.IF_AP)
ap.config(ssid='control', password='lightcontrol', authmode=network.AUTH_WPA_WPA2_PSK)
#ap.config(key='light')
#ap.config(security=)
ap.active(True)