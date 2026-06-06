"""
flare.shapes — 2-D shape primitives with color support.
"""
from __future__ import annotations
import math
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .core import Canvas, Color


def _line_pixels(x0,y0,x1,y1):
    pixels=[]
    dx,dy=abs(x1-x0),abs(y1-y0)
    sx=1 if x0<x1 else -1
    sy=1 if y0<y1 else -1
    err=dx-dy
    x,y=x0,y0
    while True:
        pixels.append((x,y))
        if x==x1 and y==y1: break
        e2=2*err
        if e2>-dy: err-=dy; x+=sx
        if e2<dx:  err+=dx; y+=sy
    return pixels


def draw_pixel(canvas:"Canvas", x:int, y:int, value:float=1.0, color:"Color|None"=None):
    """Draw a single pixel."""
    canvas.set_pixel(x, y, value, color)


def draw_line(canvas:"Canvas", x0:int, y0:int, x1:int, y1:int, value:float=1.0, color:"Color|None"=None):
    """Draw a straight line."""
    for x,y in _line_pixels(x0,y0,x1,y1):
        canvas.set_pixel(x, y, value, color)


def draw_rect(canvas:"Canvas", x:int, y:int, w:int, h:int, filled:bool=False, value:float=1.0, color:"Color|None"=None):
    """Draw a rectangle."""
    if filled:
        for ry in range(y, y+h):
            for rx in range(x, x+w):
                canvas.set_pixel(rx, ry, value, color)
    else:
        draw_line(canvas,x,y,x+w-1,y,value,color)
        draw_line(canvas,x,y+h-1,x+w-1,y+h-1,value,color)
        draw_line(canvas,x,y,x,y+h-1,value,color)
        draw_line(canvas,x+w-1,y,x+w-1,y+h-1,value,color)


def draw_circle(canvas:"Canvas", cx:int, cy:int, radius:int, filled:bool=False, value:float=1.0, color:"Color|None"=None):
    """Draw a circle."""
    if filled:
        for y in range(cy-radius, cy+radius+1):
            for x in range(cx-radius, cx+radius+1):
                if (x-cx)**2+(y-cy)**2<=radius**2:
                    canvas.set_pixel(x,y,value,color)
    else:
        x,y,err=radius,0,0
        while x>=y:
            for px,py in [(cx+x,cy+y),(cx-x,cy+y),(cx+x,cy-y),(cx-x,cy-y),
                          (cx+y,cy+x),(cx-y,cy+x),(cx+y,cy-x),(cx-y,cy-x)]:
                canvas.set_pixel(px,py,value,color)
            y+=1; err+=2*y+1
            if err>2*x: x-=1; err-=2*x+1


def draw_ellipse(canvas:"Canvas", cx:int, cy:int, rx:int, ry:int, filled:bool=False, value:float=1.0, color:"Color|None"=None):
    """Draw an ellipse."""
    if filled:
        for y in range(cy-ry, cy+ry+1):
            for x in range(cx-rx, cx+rx+1):
                if (x-cx)**2/max(rx,1)**2+(y-cy)**2/max(ry,1)**2<=1:
                    canvas.set_pixel(x,y,value,color)
    else:
        steps=max(rx,ry)*8
        for i in range(steps):
            t=2*math.pi*i/steps
            canvas.set_pixel(int(cx+rx*math.cos(t)), int(cy+ry*math.sin(t)), value, color)


def draw_triangle(canvas:"Canvas", x0,y0,x1,y1,x2,y2, filled:bool=False, value:float=1.0, color:"Color|None"=None):
    """Draw a triangle."""
    if filled:
        pts=sorted([(x0,y0),(x1,y1),(x2,y2)],key=lambda p:p[1])
        (ax,ay),(bx,by),(cx2,cy2)=pts
        for scan_y in range(ay,cy2+1):
            def _xa(ya,xa,yb,xb):
                if ya==yb: return None
                t=(scan_y-ya)/(yb-ya)
                return xa+t*(xb-xa) if 0<=t<=1 else None
            xs=[v for v in [_xa(ay,ax,cy2,cx2),_xa(ay,ax,by,bx),_xa(by,bx,cy2,cx2)] if v is not None]
            if len(xs)>=2:
                for fill_x in range(int(min(xs)),int(max(xs))+1):
                    canvas.set_pixel(fill_x,scan_y,value,color)
    else:
        draw_line(canvas,x0,y0,x1,y1,value,color)
        draw_line(canvas,x1,y1,x2,y2,value,color)
        draw_line(canvas,x2,y2,x0,y0,value,color)


def draw_polygon(canvas:"Canvas", points:list, filled:bool=False, value:float=1.0, color:"Color|None"=None):
    """Draw a polygon from a list of (x,y) points."""
    if len(points)<2: return
    if filled:
        ys=[p[1] for p in points]
        miny,maxy=min(ys),max(ys)
        n=len(points)
        for scan_y in range(miny,maxy+1):
            xs=[]
            for i in range(n):
                x0,y0=points[i]; x1,y1=points[(i+1)%n]
                if y0==y1: continue
                if min(y0,y1)<=scan_y<max(y0,y1):
                    t=(scan_y-y0)/(y1-y0)
                    xs.append(x0+t*(x1-x0))
            xs.sort()
            for j in range(0,len(xs)-1,2):
                for fill_x in range(int(xs[j]),int(xs[j+1])+1):
                    canvas.set_pixel(fill_x,scan_y,value,color)
    else:
        for i in range(len(points)):
            x0,y0=points[i]; x1,y1=points[(i+1)%len(points)]
            draw_line(canvas,x0,y0,x1,y1,value,color)


def draw_text(canvas:"Canvas", x:int, y:int, text:str, color:"Color|None"=None, charset=None):
    """Draw ASCII text using a 3×5 bitmap font."""
    _render_text_pixels(canvas, x, y, text, color)


def draw_bezier(canvas:"Canvas", points:list, steps:int=200, value:float=1.0, color:"Color|None"=None):
    """Draw a Bézier curve through control points."""
    def _pt(t):
        pts=list(points)
        while len(pts)>1:
            pts=[(pts[i][0]*(1-t)+pts[i+1][0]*t, pts[i][1]*(1-t)+pts[i+1][1]*t) for i in range(len(pts)-1)]
        return pts[0]
    prev=None
    for i in range(steps+1):
        pt=_pt(i/steps)
        ix,iy=int(pt[0]),int(pt[1])
        if prev and prev!=(ix,iy):
            draw_line(canvas,prev[0],prev[1],ix,iy,value,color)
        prev=(ix,iy)


def draw_gradient_rect(canvas:"Canvas", x:int, y:int, w:int, h:int,
                       color_a:"Color", color_b:"Color",
                       direction:str="horizontal"):
    """Draw a filled rectangle blending from color_a to color_b."""
    from .core import Color
    for ry in range(y, y+h):
        for rx in range(x, x+w):
            if direction=="horizontal":
                t=(rx-x)/max(w-1,1)
            else:
                t=(ry-y)/max(h-1,1)
            col=color_a.lerp(color_b, t)
            canvas.set_pixel(rx, ry, 1.0, col)


# ── 3×5 bitmap font ──────────────────────────────────────────────────────────

_FONT: dict[str, list[str]] = {
    "A":["010","101","111","101","101"],"B":["110","101","110","101","110"],
    "C":["011","100","100","100","011"],"D":["110","101","101","101","110"],
    "E":["111","100","110","100","111"],"F":["111","100","110","100","100"],
    "G":["011","100","101","101","011"],"H":["101","101","111","101","101"],
    "I":["111","010","010","010","111"],"J":["001","001","001","101","010"],
    "K":["101","101","110","101","101"],"L":["100","100","100","100","111"],
    "M":["101","111","101","101","101"],"N":["101","111","111","101","101"],
    "O":["010","101","101","101","010"],"P":["110","101","110","100","100"],
    "Q":["010","101","101","011","001"],"R":["110","101","110","101","101"],
    "S":["011","100","010","001","110"],"T":["111","010","010","010","010"],
    "U":["101","101","101","101","010"],"V":["101","101","101","010","010"],
    "W":["101","101","101","111","101"],"X":["101","101","010","101","101"],
    "Y":["101","101","010","010","010"],"Z":["111","001","010","100","111"],
    "0":["010","101","101","101","010"],"1":["010","110","010","010","111"],
    "2":["110","001","010","100","111"],"3":["110","001","010","001","110"],
    "4":["101","101","111","001","001"],"5":["111","100","110","001","110"],
    "6":["010","100","110","101","010"],"7":["111","001","010","010","010"],
    "8":["010","101","010","101","010"],"9":["010","101","011","001","010"],
    " ":["000","000","000","000","000"],".":["000","000","000","000","010"],
    "!":["010","010","010","000","010"],"?":["110","001","010","000","010"],
    "-":["000","000","111","000","000"],"_":["000","000","000","000","111"],
    "+":["000","010","111","010","000"],"*":["101","010","111","010","101"],
    "/":["001","001","010","100","100"],"\\": ["100","100","010","001","001"],
    ":":["000","010","000","010","000"],",":["000","000","000","010","100"],
}


def _render_text_pixels(canvas:"Canvas", x:int, y:int, text:str, color=None):
    cx=x
    for ch in text.upper():
        rows=_FONT.get(ch, _FONT.get("?",[" "*3]*5))
        for row_i,row in enumerate(rows):
            for col_i,bit in enumerate(row):
                if bit=="1":
                    canvas.set_pixel(cx+col_i, y+row_i, 1.0, color)
        cx+=4
