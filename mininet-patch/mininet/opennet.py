#!/usr/bin/python

import os
import ns.netanim
import ns.csma
import ns.wifi

def checkDictionaryPath(path):
    """ Check dictionary exist or not, if not create it """
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    return path


class Netanim( object ):
    def __init__(self, path="/tmp/xml/wifi-wired-bridged4.xml", nodes=None, packetmetadata=True):
        self.path = path
        self.packetmetadata = packetmetadata
        self.nodes = nodes
        self.netanim = self.Netanim()

    def __str__(self):
        return repr(self)

    def __repr__(self):
        path_str = "Netanim path: %s" % self.getNetanimPath()
        return path_str

    def Netanim(self):
        """ Enable netanim output """
        checkDictionaryPath(self.path)
        netanim = ns.netanim.AnimationInterface(self.path)
        netanim.EnablePacketMetadata(self.packetmetadata)
        return netanim

    def getNetanimPath(self):
        return self.path

    def UpdateNodeDescription(self, node, desc):
        self.netanim.UpdateNodeDescription(node, desc)
        return True

    def UpdateNodeColor(self, node, r, g, b):
        self.netanim.UpdateNodeColor(node, r, g, b)
        return True

class Pcap( object ):
    def __init__(self, wifi_pcap_path="/tmp/pcap/wifi", csma_pcap_path="/tmp/pcap/csma"):
        self.wifi_pcap_path = wifi_pcap_path
        self.csma_pcap_path = csma_pcap_path

    def __str__(self):
        return repr(self)

    def __repr__(self):
        pcap_path = "Wifi pcap path: %s\nCSMA pcap path:%s" % (self.getWifiPath(), self.getCSMAPath())
        return pcap_path

    def setWifiPath(self, path):
        checkDictionaryPath(path)
        self.wifi_pcap_path = checkDictionaryPath(path)
        return True

    def setCSMAPath(self, path):
        checkDictionaryPath(path)
        self.csma_pcap_path = path
        return True

    def getWifiPath(self):
        return self.wifi_pcap_path

    def getCSMAPath(self):
        return self.csma_pcap_path

    def enable(self):

        """ Setting Wifi pcap """
        self.setWifiPath(self.wifi_pcap_path)
        ns.wifi.YansWifiPhyHelper().Default().EnablePcapAll(self.wifi_pcap_path)

        """ Setting CSMA pcap """
        self.setCSMAPath(self.csma_pcap_path)
        ns.csma.CsmaHelper().EnablePcapAll(self.csma_pcap_path)

        return True


