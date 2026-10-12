OPENQASM 2.0;
include "qelib1.inc";
qreg q[4];
h q[0];
cx q[0],q[3];
cx q[1],q[2];
rz(0.25) q[1];
