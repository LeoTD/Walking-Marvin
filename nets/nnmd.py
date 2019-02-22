import numpy as np
from actor import Actor
from math import tanh
import random as rand

class NeuralNetMD:
    def __init__(self):
        pass

    def compute_action(self, actor, inputs):
        return self.net(actor.W, actor.B, inputs)
        
    def sum_w_b(self, weights, biases, inputs):
        output = 0.0
        assert len(weights) == len(inputs) and len(biases) == len(inputs)
        for i in range(len(inputs)):
            output = output + inputs[i] * weights[i] + biases[i]
        return output / 10

    #takes 144W, 72B, 24S.
    def net(self, W, B, inputs):
        Hull_data = self.compute_hulls(W[624:632], B[624:632], inputs[0:4])
        Li_data = self.compute_lidar(inputs[14:24])
        return self.fc_net(W[0:624], B[0:624], Hull_data + tuple(inputs[4:8]) + tuple(inputs[9:13]), Li_data, inputs[8], inputs[13])


    def fc_net(self, W, B, S, Li, Lc1, Lc2):
        
        fc_f1 = self.fc_layer(  W[0:144], B[0:144],
                                S,
                                12,
                                self.relu,
                                self.dropout)
        fc_f1 = self.fc_layer(W[144:240], B[144:240], fc_f1, 8, self.relu)
        fc_f1 = self.fc_layer(W[240:295], B[240:295], fc_f1 + list(Li), 5, self.relu)
        fc_f1 = self.fc_layer(W[295:305], B[295:305], fc_f1, 2)
            
        fc_f2 = self.fc_layer(  W[0:144], B[0:144],
                                tuple(S[0:4]) + tuple(S[8:12]) + tuple(S[4:8]),
                                12,
                                self.relu,
                                self.dropout)
        fc_f2 = self.fc_layer(W[144:240], B[144:240], fc_f2, 8, self.relu)
        fc_f2 = self.fc_layer(W[240:295], B[240:295], fc_f2 + list(Li), 5, self.relu)
        fc_f2 = self.fc_layer(W[295:305], B[295:305], fc_f2, 2)
            
        fc_b1 = self.fc_layer(  W[305:449], B[305:449],
                                S,
                                12,
                                self.relu,
                                self.dropout)
        fc_b1 = self.fc_layer(W[449:545], B[449:545], fc_b1, 8, self.relu)
        fc_b1 = self.fc_layer(W[545:600], B[545:600], fc_b1 + list(Li), 5, self.relu)
        fc_b1 = self.fc_layer(W[600:620], B[600:620], fc_b1, 2)

        fc_b2 = self.fc_layer(  W[305:449], B[305:449],
                                tuple(S[0:4]) + tuple(S[8:12]) + tuple(S[4:8]),
                                12,
                                self.relu,
                                self.dropout)
        fc_b2 = self.fc_layer(W[449:545], B[449:545], fc_b2, 8, self.relu)
        fc_b2 = self.fc_layer(W[545:600], B[545:600], fc_b2 + list(Li), 5, self.relu)
        fc_b2 = self.fc_layer(W[600:620], B[600:620], fc_b2, 2)
        
        if Lc2 == 1:
            D1, D2 = self.leg_contact(W[620:622], B[620:622], fc_f1, Lc1)
        else:
            D1, D2 = self.leg_contact(W[622:624], B[622:624], fc_b1, Lc1)
        if Lc1 == 1:
            D3, D4 = self.leg_contact(W[620:622], B[620:622], fc_f2, Lc2)
        else:
            D3, D4 = self.leg_contact(W[622:624], B[622:624], fc_b2, Lc2)
        return D1, D2, D3, D4

    # n is number of output nodes
    # k is number of input signals
    #takes n*kW, n*kB, kS
    def fc_layer(self, W, B, S, n, A=None, D=None, D_rate=0.1):
        output = []
        for i in range(n):
            node = 0.0
            k = len(S) * i
            for j in range(len(S)):
                node += S[j] * W[j + k] + B[j + k]
            if A:
                output.append(A(node))
            else:
                output.append(node)
        if D:
            return D(output, D_rate)
        return output

    def dropout(self, N, rate):
        O = []
        for i in range(len(N)):
            if rand.randint(0, 1 // rate - 1) == 0:
                O.append(0.0)
            else:
                O.append(N[i])
        return O

    #takes 2W, 2B, 2S, 1Lc
    def leg_contact(self, W, B, S, Lc):
        O1 = tanh(S[0] + Lc * self.relu(S[0] * W[0] + B[0]))
        O2 = tanh(S[1] + Lc * self.relu(S[1] * W[1] + B[1]))
        return O1, O2

    #takes 16W, 4B, 3Li, 4Lg, 2S (leg contacts)
    def compute_combination(self, W, B, Li, Lg, S1, S2):
        if S2 < 0.5:
            D1 = tanh(Lg[0] * W[0] + Li[0] * W[1] + Li[1] * W[2] + Li[2] * W[3] + B[0])
            D2 = tanh(Lg[1] * W[4] + Li[0] * W[5] + Li[1] * W[6] + Li[2] * W[7] + B[1])
        else:
            D1 = tanh(Lg[0] * W[8] + Li[0] * W[9] + Li[1] * W[10] + Li[2] * W[11] + B[2])
            D2 = tanh(Lg[1] * W[12] + Li[0] * W[13] + Li[1] * W[14] + Li[2] * W[15] + B[3])
        if S1 < 0.5:
            D3 = tanh(Lg[2] * W[0] + Li[0] * W[1] + Li[1] * W[2] + Li[2] * W[3] + B[0])
            D4 = tanh(Lg[3] * W[4] + Li[0] * W[5] + Li[1] * W[6] + Li[2] * W[7] + B[1])
        else:
            D3 = tanh(Lg[2] * W[8] + Li[0] * W[9] + Li[1] * W[10] + Li[2] * W[11] + B[2])
            D4 = tanh(Lg[3] * W[12] + Li[0] * W[13] + Li[1] * W[14] + Li[2] * W[15] + B[3])
        return D1, D2, D3, D4

    #takes 8W, 8B, 4S.
    def compute_hulls(self, W, B, S):
        Hull_A = self.relu_sum(W[0:2], B[0:2], S[0])
        Hull_B = self.relu_sum(W[2:4], B[2:4], S[1])
        Hull_C = self.relu_sum(W[4:6], B[4:6], S[2])
        Hull_D = self.relu_sum(W[6:8], B[6:8], S[3])
        return Hull_A, Hull_B, Hull_C, Hull_D

    #takes, 64W, 36B, 10S, 4H.
    def compute_legs(self, W, B, S, H):
        if S[9] < 0.5:
            L1a, L2a = self.leg_net(W[0:14], B[0:7], S[0], S[2], H[0:2])
            L1b, L2b = self.leg_net(W[14:28], B[7:14], S[1], S[3], H[2:4])
        else:
            L1a, L2a = self.leg_net(W[28:42], B[14:21], S[0], S[2], H[0:2])
            L1b, L2b = self.leg_net(W[42:56], B[21:28], S[1], S[3], H[2:4])
        if S[4] < 0.5:
            L3a, L4a = self.leg_net(W[0:14], B[0:7], S[5], S[7], H[0:2])
            L3b, L4b = self.leg_net(W[14:28], B[7:14], S[6], S[8], H[2:4])
        else:
            L3a, L4a = self.leg_net(W[28:42], B[14:21], S[5], S[7], H[0:2])
            L3b, L4b = self.leg_net(W[42:56], B[21:28], S[6], S[8], H[2:4])
        L1 = tanh(L1a + L1b)
        L2 = tanh(L2a + L2b)
        L3 = tanh(L3a + L3b)
        L4 = tanh(L4a + L4b)
        if S[9] < 0.5:
            L1 = tanh(L1 + S[4] * self.relu(L1 * W[56] + B[28]))
            L2 = tanh(L2 + S[4] * self.relu(L2 * W[57] + B[29]))
        else:
            L1 = tanh(L1 + S[4] * self.relu(L1 * W[58] + B[30]) + H[1] * W[60] + B[32])    #ADD HULL ANGLE HERE
            L2 = tanh(L2 + S[4] * self.relu(L2 * W[59] + B[31]) + H[1] * W[61] + B[33])    #HERE
        if S[4] < 0.5:
            L3 = tanh(L3 + S[9] * self.relu(L3 * W[56] + B[28]))
            L4 = tanh(L4 + S[9] * self.relu(L4 * W[57] + B[29]))
        else:
            L3 = tanh(L3 + S[9] * self.relu(L3 * W[58] + B[30]) + H[3] * W[62] + B[34])    #HERE
            L4 = tanh(L4 + S[9] * self.relu(L4 * W[59] + B[31]) + H[3] * W[63] + B[35])    #AND HERE
        return L1, L2, L3, L4

    #takes 14W, 7B, 2S, 2H
    def leg_net(self, W, B, S1, S2, H):
        J1 = tanh(self.relu_sum(W[0:2], B[0:2], S1))
        J2 = tanh(self.relu_sum(W[2:4], B[2:4], S2))
        tmp = self.relu(J1 * W[4] + J2 * W[5] + B[4])
        J1 = tanh(J1 * W[6] + tmp * W[7] + H[0] * W[8] + H[1] * W[9] + B[5])
        J2 = tanh(J2 * W[10] + tmp * W[11] + H[0] * W[12] + H[1] * W[13] + B[6])
        return J1, J2

    #takes 60W, 28B, four signals.
    def output_layer(self, W, B, D):
    
        O1 = self.outlay_1(W[0:6], B[0:3], D[0], D[1], D[2], D[3])
        O2 = self.outlay_1(W[6:12], B[3:6], D[1], D[0], D[2], D[3])
        O3 = self.outlay_1(W[12:18], B[6:9], D[2], D[1], D[0], D[3])
        O4 = self.outlay_1(W[18:24], B[9:12], D[3], D[1], D[2], D[0])
        
        O1 = self.outlay_2(W[24:30], B[12:15], O1)
        O2 = self.outlay_2(W[30:36], B[15:18], O2)
        O3 = self.outlay_2(W[36:42], B[18:21], O3)
        O4 = self.outlay_2(W[42:48], B[21:24], O4)

        O1 = self.outlay_3(W[48:51], B[24], O1, D[0])
        O2 = self.outlay_3(W[51:54], B[25], O2, D[1])
        O3 = self.outlay_3(W[54:57], B[26], O3, D[2])
        O4 = self.outlay_3(W[57:60], B[27], O4, D[3])

        return O1, O2, O3, O4

    #takes 6W, 3B, 4S.
    def outlay_1(self, W, B, s1, s2, s3, s4):
        o1 = self.relu(s1 * W[0] + s2 * W[1] + B[0])
        o2 = self.relu(s1 * W[2] + s3 * W[3] + B[1])
        o3 = self.relu(s1 * W[4] + s4 * W[5] + B[2])
        return o1, o2, o3
    
    #takes 6W, 3B, 3S.
    def outlay_2(self, W, B, S):
        o1 = self.relu(S[0] * W[0] + S[1] * W[1] + B[0])
        o2 = self.relu(S[0] * W[2] + S[2] * W[3] + B[1])
        o3 = self.relu(S[1] * W[4] + S[2] * W[5] + B[2])
        return o1, o2, o3

    #takes 3W, 1B, 3S.
    def outlay_3(self, W, B, S, D):
        return tanh(D + S[0] * W[0] + S[1] * W[1] + S[2] * W[2] + B)

    #reduces 10Lidar signals to three. Similar to a 1d conv. One unit signal overlap
    def compute_lidar(self, S):
        Li_top = tanh(S[0] + S[1] + S[2] + S[3])
        Li_mid = tanh(S[3] + S[4] + S[5] + S[6])
        Li_bot = tanh(S[6] + S[7] + S[8] + S[9])
        return Li_top, Li_mid, Li_bot

    #takes 2W, 2B, 1S. Sum of signal through weight/bias with same signal through ReLu.
    #puts result through tanh.
    def relu_sum(self, W, B, S):
        output = S * W[0] + B[0]
        output += self.relu(S * W[1] + B[1])
        return tanh(output)

    def relu(self, x):
        return x * (x > 0)
