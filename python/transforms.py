import math

SQRT3_OVER_2 = 0.8660254037844386

def clarke_transform(ia, ib, ic):
    ialpha = (2/3) * (ia - 0.5*ib - 0.5*ic)
    ibeta = (2/3) * SQRT3_OVER_2 * (ib - ic)
    return ialpha, ibeta

def clarke_inverse_transform(ialpha, ibeta):
    ia = ialpha
    ib = -0.5*ialpha + SQRT3_OVER_2*ibeta
    ic = -0.5*ialpha - SQRT3_OVER_2*ibeta
    return ia, ib, ic

def park_transform(ialpha, ibeta, theta):
    c, s = math.cos(theta), math.sin(theta)
    id_ = ialpha*c + ibeta*s
    iq  = -ialpha*s + ibeta*c
    return id_, iq

def park_inverse_transform(vd, vq, theta):
    c, s = math.cos(theta), math.sin(theta)
    valpha = vd*c - vq*s
    vbeta  = vd*s + vq*c
    return valpha, vbeta