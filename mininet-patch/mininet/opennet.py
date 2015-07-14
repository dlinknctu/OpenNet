#!/usr/bin/python

import os
import ns.netanim


class netanim( object ):
    def __init__(self, path=None, nodes=None, packetmetadata=True):
        self.path = path
        self.packetmetadata = packetmetadata
        self.nodes = nodes
        self.netanim = self.Netanim()

    def Netanim(self):
        """ Enable netanim output """

        # Check dictionary exist or not, if not create it
        if not os.path.exists(os.path.dirname(self.path)):
            os.makedirs(os.path.dirname(self.path))

        netanim = ns.netanim.AnimationInterface(self.path)
        netanim.EnablePacketMetadata(self.packetmetadata)
        return netanim

    def UpdateNodeDescription(self, node, desc):
        self.netanim.UpdateNodeDescription(node, desc)

    def UpdateNodeColor(self, node, r, g, b):
        self.netanim.UpdateNodeColor(node, r, g, b)

