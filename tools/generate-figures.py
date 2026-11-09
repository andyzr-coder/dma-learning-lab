"""原创课程图的共同 SVG / PNG 渲染器。仅依赖 Pillow，不复制课程 PDF 图。"""
from pathlib import Path
import json, math, html, itertools
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'public/figures'
OUT.mkdir(parents=True, exist_ok=True)
INK='#172b3a'; MUTED='#526676'; TEAL='#087f8c'; BLUE='#3169b3'; ORANGE='#b66a16'; RED='#b53d43'; GREEN='#23734c'; PAPER='#ffffff'; LIGHT='#edf5f7'; GRID='#c9d6df'
FONT='C:/Windows/Fonts/msyh.ttc'; BOLD='C:/Windows/Fonts/msyhbd.ttc'
MANIFEST=[]; CHECKS=[]

class Canvas:
    def __init__(self,id,module,title,subtitle,w=1200,h=820):
        self.id=id; self.module=module;self.title=title;self.w=w;self.h=h
        self.im=Image.new('RGB',(w*2,h*2),PAPER);self.d=ImageDraw.Draw(self.im);self.svg=[];self.fonts={}
        self.rect(0,0,w,h,fill=PAPER,stroke=None)
        self.rect(0,0,w,95,fill='#e7f2f4',stroke=None)
        self.text(36,22,title,32,bold=True)
        self.text(38,66,subtitle,18,fill=MUTED)
    def font(self,size,bold=False):
        k=(size,bold)
        if k not in self.fonts:self.fonts[k]=ImageFont.truetype(BOLD if bold else FONT,size*2)
        return self.fonts[k]
    def text(self,x,y,text,size=22,fill=INK,bold=False,anchor='start'):
        # y is the top of a text line in both renderers.
        text=str(text); f=self.font(size,bold); width=self.d.textlength(text,font=f)/2
        px=x if anchor=='start' else x-width/2 if anchor=='middle' else x-width
        self.d.text((px*2,y*2),text,font=f,fill=fill,anchor='lt')
        self.svg.append(f'<text x="{x}" y="{y}" dominant-baseline="text-before-edge" text-anchor="{anchor}" font-size="{size}" font-weight="{700 if bold else 400}" fill="{fill}">{html.escape(text)}</text>')
        if px < -1 or px+width > self.w+1:CHECKS.append({'figure':self.id,'warning':'text width','text':text,'x':px,'right':px+width})
    def lines(self,x,y,lines,size=22,fill=INK,gap=None,bold=False):
        for i,t in enumerate(lines):self.text(x,y+i*(gap or size*1.5),t,size,fill,bold)
    def rect(self,x,y,w,h,fill=PAPER,stroke=GRID,r=0,lw=2):
        box=(x*2,y*2,(x+w)*2,(y+h)*2)
        self.d.rounded_rectangle(box,radius=r*2,fill=fill,outline=stroke,width=lw*2) if r else self.d.rectangle(box,fill=fill,outline=stroke,width=lw*2)
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill or "none"}" stroke="{stroke or "none"}" stroke-width="{lw}"/>')
    def circle(self,x,y,r,fill=PAPER,stroke=INK,lw=2):
        self.d.ellipse(((x-r)*2,(y-r)*2,(x+r)*2,(y+r)*2),fill=fill,outline=stroke,width=lw*2)
        self.svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill or "none"}" stroke="{stroke}" stroke-width="{lw}"/>')
    def poly(self,points,fill):
        self.d.polygon([(x*2,y*2) for x,y in points],fill=fill)
        self.svg.append(f'<polygon points="{" ".join(f"{x},{y}" for x,y in points)}" fill="{fill}"/>')
    def line(self,points,color=INK,lw=3,arrow=False,dash=False):
        for (x1,y1),(x2,y2) in zip(points,points[1:]):
            if dash:
                dist=math.hypot(x2-x1,y2-y1)
                for t in range(0,int(dist),14):
                    a=t/dist;b=min(t+8,dist)/dist
                    self.d.line((2*(x1+(x2-x1)*a),2*(y1+(y2-y1)*a),2*(x1+(x2-x1)*b),2*(y1+(y2-y1)*b)),fill=color,width=lw*2)
            else:self.d.line([(x1*2,y1*2),(x2*2,y2*2)],fill=color,width=lw*2)
        self.svg.append(f'<polyline points="{" ".join(f"{x},{y}" for x,y in points)}" fill="none" stroke="{color}" stroke-width="{lw}" stroke-linejoin="round" {"stroke-dasharray=\"8 6\"" if dash else ""}/>')
        if arrow and len(points)>1:
            x,y=points[-1];px,py=points[-2];a=math.atan2(y-py,x-px);s=10
            self.poly([(x,y),(x-s*math.cos(a)+s*.5*math.sin(a),y-s*math.sin(a)-s*.5*math.cos(a)),(x-s*math.cos(a)-s*.5*math.sin(a),y-s*math.sin(a)+s*.5*math.cos(a))],color)
    def box(self,x,y,w,h,title,body=None,color=TEAL):
        self.rect(x,y,w,h,fill=LIGHT,stroke=color,r=12)
        self.text(x+w/2,y+16,title,24,fill=color,bold=True,anchor='middle')
        if body:self.lines(x+18,y+57,body,20)
    def gate(self,x,y,label,w=100,h=84):
        self.rect(x,y,w,h,fill=LIGHT,stroke=TEAL,r=10,lw=3)
        self.text(x+w/2,y+15,label,25,fill=TEAL,bold=True,anchor='middle')
        self.text(x+w/2,y+48,'逻辑门',16,fill=MUTED,anchor='middle')
    def table(self,x,y,headers,rows,widths,rh=42,colors=None,size=21):
        for row_i,row in enumerate([headers]+rows):
            xx=x
            for col_i,(t,w) in enumerate(zip(row,widths)):
                fill='#dfedf0' if row_i==0 else (colors or {}).get(row_i-1,PAPER)
                self.rect(xx,y+row_i*rh,w,rh,fill=fill,stroke=GRID,lw=1)
                self.text(xx+w/2,y+row_i*rh+(rh-size)/2-1,str(t),size,bold=row_i==0,anchor='middle')
                xx+=w
    def save(self,alt,caption):
        self.line([(36,self.h-54),(self.w-36,self.h-54)],GRID,1)
        self.text(36,self.h-40,'原创教学图 · 据课程机制重新构造 · '+' / '.join([self.module.upper(),self.id]),15,fill=MUTED)
        svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" role="img"><title>{html.escape(self.title)}</title><desc>{html.escape(alt)}</desc><g font-family="Microsoft YaHei, Noto Sans CJK SC, sans-serif">'+''.join(self.svg)+'</g></svg>'
        (OUT/(self.id+'.svg')).write_text(svg,encoding='utf-8');self.im.save(OUT/(self.id+'.png'))
        MANIFEST.append({'id':self.id,'module':self.module,'title':self.title,'alt':alt,'caption':caption,'svg':'figures/'+self.id+'.svg','png':'figures/'+self.id+'.png','width':self.w,'height':self.h})

def front01():
    c=Canvas('front-m01-flow','m01','一张真值表如何变成电路？','约定：abc 为输入顺序；a 是最高位；+ 是 OR，连写是 AND。')
    c.text(50,125,'① 逐行规定行为',26,bold=True)
    rows=[]
    for v in range(8):
        a,b,z=(v>>2)&1,(v>>1)&1,v&1;rows.append([v,a,b,z,a&b,(a&b)|z])
    c.table(50,175,['m','a','b','c','n','f'],rows,[50]*6,rh=43,colors={1:'#e3f5ed',3:'#e3f5ed',5:'#e3f5ed',6:'#e3f5ed',7:'#e3f5ed'})
    c.text(50,590,'ON-set = {1, 3, 5, 6, 7}',22,fill=GREEN,bold=True)
    c.text(430,125,'② 方程：f = ab + c',26,bold=True)
    c.text(650,180,'③ 连接门与导线',26,bold=True)
    c.gate(720,265,'AND');c.gate(960,330,'OR')
    c.text(610,268,'a',24);c.text(610,318,'b',24);c.text(610,450,'c',24)
    c.line([(640,285),(720,285)],arrow=True);c.line([(640,330),(720,330)],arrow=True)
    c.line([(820,307),(900,307),(900,350),(960,350)],arrow=True)
    c.text(845,267,'n = ab',20,fill=TEAL)
    c.line([(640,468),(900,468),(900,395),(960,395)],arrow=True)
    c.line([(1060,372),(1150,372)],arrow=True);c.text(1085,325,'f',25,bold=True)
    c.box(430,550,720,170,'④ 用一行核验门图',['输入 abc = 110：AND 得 n = 1；OR 得 1 OR 0 = 1。','输入 abc = 001：AND 得 n = 0；OR 得 0 OR 1 = 1。','把 8 行全验完，才证明此组合电路与真值表等价。'])
    c.save('左侧为abc的8行真值表，f依次是0、1、0、1、0、1、1、1；右侧a和b进入AND，其输出与c进入OR。','真值表规定功能，方程表达功能，门图给出一种实现。这里只画理想组合逻辑，未指定工艺、物理延迟或电源。')

def front01_extra():
    c=Canvas('front-m01-ychart','m01','Y-chart：三个观察域 × 五个抽象层级','按 L25 Introduction 印刷 pp.5–6 / PDF pp.9–10 的机制原创重绘；外圈更抽象，向中心逐步细化。',1400,1000)
    cx,cy=330,440
    for rad in [75,120,165,210,255]:c.circle(cx,cy,rad,fill=None,stroke=GRID,lw=2)
    for pt in [(75,185),(585,185),(330,765)]:c.line([(cx,cy),pt],TEAL,4,arrow=True)
    c.text(45,130,'行为域：做什么？',26,fill=TEAL,bold=True)
    c.text(395,130,'结构域：怎样连接？',26,fill=TEAL,bold=True)
    c.text(330,785,'物理域：放在哪里？',26,fill=TEAL,bold=True,anchor='middle')
    for i,rad in enumerate([75,120,165,210,255],1):
        c.circle(cx,cy+rad,18,fill=PAPER,stroke=TEAL);c.text(cx,cy+rad-14,i,21,bold=True,anchor='middle')
    c.circle(cx,cy,8,fill=TEAL,stroke=TEAL)
    rows=[['5 系统','系统规格','CPU / 存储器','芯片 / 板'],['4 算法','算法','处理器 / 子系统','块 / 芯片'],['3 RT','寄存器传输','ALU / 寄存器','宏单元'],['2 逻辑','布尔方程','门 / 触发器','单元布局'],['1 电路','微分方程','晶体管','掩模多边形']]
    c.table(650,190,['层级','行为','结构','物理'],rows,[150,175,205,165],rh=72,size=21)
    c.box(650,670,695,170,'域与层级不是同一个维度',['逻辑层的同一个设计，可以同时有：','① 布尔方程 ② 门级网表 ③ 单元与连线布局。','综合/分析可以跨域；细化/抽象可以跨层。'])
    c.text(70,890,'图上的轴不是流水线步骤；“结构域”也不等于“低抽象层”。实际设计会反复验证与反馈。',24,bold=True)
    c.save('Y形三轴分别为行为、结构、物理；五个同心层从内到外为电路、逻辑、RT、算法、系统。右表给每个层级在三个域中的典型对象。','沿同一圈切换观察域，沿径向改变抽象层级。对应关系据课程Y-chart与Design Space页，示意距离没有定量单位。')
    c=Canvas('front-m01-adder','m01','全加器：同一进位功能，关键路径可以不同','模型：XOR 延迟 2；AND、OR 延迟 1；输入同时到达，忽略导线，右图允许三输入 OR。',1400,1080)
    c.text(350,130,'方案 A：共享 p = a XOR b',28,bold=True,anchor='middle')
    c.text(1050,130,'方案 B：多数函数 carry',28,bold=True,anchor='middle')
    c.line([(700,115),(700,735)],GRID,1)
    # Shared propagate: p feeds sum and carry path, independent ab feeds carry OR.
    c.gate(180,240,'XOR',95,80);c.gate(470,195,'XOR',95,80)
    c.text(55,235,'a',24);c.text(55,295,'b',24)
    c.line([(80,255),(180,255)],arrow=True);c.line([(80,305),(180,305)],arrow=True)
    c.line([(275,280),(350,280),(350,215),(470,215)],BLUE,4,arrow=True);c.text(305,235,'p',24,fill=BLUE,bold=True)
    c.line([(565,235),(650,235)],arrow=True);c.text(590,190,'s',26,bold=True)
    c.text(365,300,'cin',24);c.line([(415,330),(440,330),(440,255),(470,255)],arrow=True)
    c.gate(390,390,'AND',95,80);c.gate(160,555,'AND',95,80);c.gate(555,500,'OR',95,90)
    c.circle(350,280,5,fill=BLUE,stroke=BLUE);c.line([(350,280),(350,410),(390,410)],BLUE,4,arrow=True)
    c.text(205,445,'cin',24);c.line([(260,460),(390,450)],arrow=True)
    c.text(45,555,'a',24);c.text(45,615,'b',24);c.line([(80,575),(160,575)],arrow=True);c.line([(80,625),(160,625)],arrow=True)
    c.line([(485,430),(520,430),(520,520),(555,520)],BLUE,4,arrow=True)
    c.line([(255,595),(420,595),(420,570),(555,570)],arrow=True)
    c.line([(650,545),(680,545)],BLUE,4,arrow=True);c.text(560,635,'cout = ab + p·cin',23,bold=True,anchor='middle')
    # Majority carry with three explicit ANDs and one three-input OR.
    for y,ins in [(220,('a','b')),(380,('a','cin')),(540,('b','cin'))]:
        c.gate(900,y,'AND',95,80)
        for k,t in enumerate(ins):c.text(775,y+8+k*45,t,24);c.line([(825,y+20+k*45),(900,y+20+k*45)],arrow=True)
    c.gate(1190,360,'OR',100,140);c.text(1240,450,'3 输入',17,anchor='middle')
    c.line([(995,260),(1080,260),(1080,385),(1190,385)],GREEN,4,arrow=True)
    c.line([(995,420),(1190,420)],GREEN,4,arrow=True)
    c.line([(995,580),(1080,580),(1080,470),(1190,470)],GREEN,4,arrow=True)
    c.line([(1290,430),(1360,430)],GREEN,4,arrow=True);c.text(1300,380,'cout',23,bold=True)
    c.text(1050,665,'cout = ab + a·cin + b·cin',25,bold=True,anchor='middle')
    c.box(55,760,625,150,'A 的 carry 最长路径：2+1+1 = 4',['蓝色路径：a/b → XOR → AND → OR。','sum 已需要 p，carry 共享它可能节约逻辑。','但共享会让 carry 等待 p 生成。'])
    c.box(735,760,610,150,'B 的 carry 最长路径：1+1 = 2',['绿色路径：任意输入 → AND → 三输入 OR。','这里只比较 carry；sum 仍必须实现。','若只允许二输入 OR，最坏路径要重算。'])
    c.text(65,955,'功能核验：对全部 8 个输入，应满足整数等式 a+b+cin = s+2·cout；不要把整数 + 当布尔 OR。',23,bold=True)
    c.save('左图共享XOR的p信号给sum和carry，carry关键路径XOR-AND-OR为4时间单位。右图三个AND接三输入OR实现多数函数carry，路径2时间单位。','这是固定门模型下的延迟估算，不是纳秒或实测；右图只画carry部分，不能直接拿其门数与左图完整全加器比较面积。')

def front02():
    c=Canvas('front-m02-kmap','m02','K-map：圈的是相邻输入，留下不变变量','仍用 f = ab + c；列按 Gray 顺序 00、01、11、10，首尾也相邻。')
    c.text(80,130,'把 8 行真值表折成 2 × 4 方格',26,bold=True)
    c.text(60,235,'a',25,bold=True);c.text(205,178,'bc →',23)
    xs=[240,420,600,780]; ys=[285,425]; vals=[[0,1,1,0],[0,1,1,1]];mins=[[0,1,3,2],[4,5,7,6]]
    for j,l in enumerate(['00','01','11','10']):c.text(xs[j],225,l,25,bold=True,anchor='middle')
    for i in range(2):
        c.text(100,ys[i]+25,str(i),26,bold=True)
        for j in range(4):
            c.rect(xs[j]-80,ys[i],160,120,fill=LIGHT if vals[i][j] else PAPER)
            c.text(xs[j],ys[i]+16,str(vals[i][j]),32,bold=True,anchor='middle')
            c.text(xs[j],ys[i]+72,'m'+str(mins[i][j]),18,fill=MUTED,anchor='middle')
    c.rect(345,275,350,280,fill=None,stroke=TEAL,r=18,lw=5)
    c.rect(515,415,350,140,fill=None,stroke=ORANGE,r=18,lw=5)
    c.text(920,295,'青色 4 格 → c',25,fill=TEAL,bold=True)
    c.lines(920,342,['a、b 都变化','只有 c = 1 不变'],20)
    c.text(920,440,'橙色 2 格 → ab',25,fill=ORANGE,bold=True)
    c.lines(920,487,['c 变化','a = b = 1 不变'],20)
    c.box(80,600,1040,130,'f = c + ab',['允许重叠：m7 同时在两圈里。每圈大小必须是 1、2、4、8…；只能圈 1 或获准的 DC。','对角线接触不算相邻；此图没有 DC。圈外的 0 不能被覆盖。'])
    c.save('两行四列K-map，a为行，bc按00、01、11、10为列。c=1的四格圈成c；a=b=1的两格圈成ab，m7重叠。','从固定变量得到乘积项；覆盖所有1且不覆盖0。图中颜色与文字标签双重标识分组。')
    c=Canvas('front-m02-cofactor','m02','Cofactor 与 Shannon：先固定 a，再选子函数','f = ab + c；f[a=0] = c，f[a=1] = b + c。')
    c.box(55,145,420,145,'a = 0：f0 = c',['把 a 替换为 0：0·b + c = c。','此时 b 对输出没有影响。'])
    c.box(55,360,420,145,'a = 1：f1 = b + c',['把 a 替换为 1：1·b + c = b + c。','此时需要 OR(b, c)。'])
    c.rect(720,230,180,250,fill=LIGHT,stroke=TEAL,r=16,lw=3)
    c.text(810,330,'MUX',30,bold=True,anchor='middle');c.text(747,253,'0',22);c.text(747,430,'1',22)
    c.line([(475,210),(600,210),(600,270),(720,270)],arrow=True)
    c.line([(475,430),(720,430)],arrow=True)
    c.line([(810,150),(810,230)],arrow=True);c.text(840,160,'选择端 a',24)
    c.line([(900,355),(1100,355)],arrow=True);c.text(1000,305,'f',28,bold=True)
    c.box(55,575,1090,140,'Shannon：f = (¬a)f0 + a f1 = (¬a)c + a(b + c)',['不是把两支直接 OR：输入 abc = 010 时，f0 = 0、f1 = 1，但 a=0，只能选 f0。','核验：a=0 得 c；a=1 得 b+c。两种 a 值覆盖所有输入，因此等式成立。'])
    c.save('左侧分别固定a为0和1得到c与b+c，接入以a为选择端的MUX；a=0选择上支，a=1选择下支。','Cofactor是把变量固定后的函数，不是求导；Shannon展开的两项带互斥选择条件。')

def front03():
    c=Canvas('front-m03-quine','m03','Quine：只能合并一个固定比特不同的 cube','ON = {0, 1, 2, 5, 6, 7}，OFF = {3, 4}，无 DC；“–”表示该位自由。')
    c.text(50,130,'六个 minterm 的相邻关系',26,bold=True)
    nodes=[('000',220,220),('001',460,220),('101',580,400),('111',460,580),('110',220,580),('010',100,400)]
    labs=['P = 00–','R = –01','T = 1–1','U = 11–','S = –10','Q = 0–0']
    for i in range(6):
        a=nodes[i];b=nodes[(i+1)%6];dx=b[1]-a[1];dy=b[2]-a[2];dist=math.hypot(dx,dy)
        c.line([(a[1]+dx/dist*43,a[2]+dy/dist*43),(b[1]-dx/dist*43,b[2]-dy/dist*43)],TEAL,4)
    for t,x,y in nodes:c.circle(x,y,43,fill=LIGHT,stroke=TEAL,lw=3);c.text(x,y-15,t,24,bold=True,anchor='middle')
    for lab,x,y in [('P = 00–',340,163),('R = –01',565,285),('T = 1–1',565,505),('U = 11–',340,620),('S = –10',90,505),('Q = 0–0',90,285)]:c.text(x,y,lab,21,fill=TEAL,bold=True,anchor='middle')
    c.box(720,145,420,185,'一条边 → 一个 1-cube',['例：000 与 001 合并为 00–。','只消去 c；留下 ¬a·¬b。','覆盖点恰好是 {0, 1}。'])
    c.box(720,365,420,240,'下一轮为什么停止？',['00– 与 0–0 的横杠位置不同。','不能“看着像”就并为 0––。','0–– 会包含 OFF 点 011。','本例 6 个 1-cube 全是 PI。'])
    c.text(70,700,'每轮保存未被继续合并的 cube；PI 是“不可再扩张”，还不等于最终必选。',24,bold=True)
    c.save('六个二进制minterm组成相邻六环，六条边标出P00–、R–01、T1–1、U11–、S–10、Q0–0。没有合法的下一轮合并。','只合并固定位置相同、恰好一个固定比特相反的两个cube。本例六个PI分别覆盖两个ON点。')
    c=Canvas('front-m03-cover','m03','PI 覆盖表：选行，覆盖每一列','行是可选择的素蕴含项；列是必须覆盖的 ON minterm。')
    patterns=['00-','0-0','-01','-10','1-1','11-'];ons=[0,1,2,5,6,7]
    match=lambda p,v:all(a=='-' or a==b for a,b in zip(p,f'{v:03b}'))
    rows=[[n+' '+p.replace('-','–')]+['●' if match(p,v) else '·' for v in ons] for n,p in zip('PQRSTU',patterns)]
    c.table(90,155,['PI / cube']+[f'm{v}' for v in ons],rows,[230]+[125]*6,rh=58,colors={0:'#e3f5ed',3:'#e3f5ed',4:'#e3f5ed'},size=25)
    c.text(110,595,'方案一：P + S + T',28,fill=GREEN,bold=True);c.text(630,595,'方案二：Q + R + U',28,fill=BLUE,bold=True)
    c.lines(110,650,['每列至少一个 ●；没有仅出现一个 ● 的列，所以没有 EPI。','每个 PI 最多盖 2 个点，要盖 6 点至少选 3 项；两方案都达下界：3 项、6 literal。'],23)
    c.save('6行6列覆盖表，P覆盖0与1，Q覆盖0与2，R覆盖1与5，S覆盖2与6，T覆盖5与7，U覆盖6与7。PST与QRU都覆盖六列。','两种最优覆盖均为3项、6 literal；无EPI不等于无解。此表的选择变量P至U不是电路输入a,b,c。')

def front04():
    c=Canvas('front-m04-trajectory','m04','启发式局部操作：每一步都检查当前 cover','固定 ON = {3, 6, 7}；只用教学示例说明 expand / remove，不宣称运行完整 Espresso。')
    steps=[('原 cover',['abc','ab¬c','¬abc'],'9 literal'),('扩张 abc → ab',['ab','ab¬c','¬abc'],'8 literal'),('删除冗余 ab¬c',['ab','¬abc'],'5 literal'),('扩张 ¬abc → bc',['ab','bc'],'4 literal')]
    for i,(title,terms,cost) in enumerate(steps):
        x=35+i*295;c.box(x,170,255,310,f'{i+1}. {title}',color=TEAL if i%2==0 else BLUE)
        for j,t in enumerate(terms):c.text(x+128,250+j*52,t,30,bold=True,anchor='middle')
        c.text(x+128,428,cost,25,fill=ORANGE,bold=True,anchor='middle')
        if i<3:c.line([(x+260,325),(x+290,325)],arrow=True)
    c.box(55,530,1090,185,'为什么合法？看新增或失去的点',['① abc→ab 只新增 110；它本来就在 ON 中。','② 删除 ab¬c 后，110 仍被 ab 覆盖，所以 ON 不丢失。','③ ¬abc→bc 只新增 111；仍在 ON 中。最后 f=ab+bc，真值没有改变。'])
    c.save('四个cover依次abc+ab¬c+¬abc、ab+ab¬c+¬abc、ab+¬abc、ab+bc，literal数量9、8、5、4。每次扩张只新增既有ON点。','轨迹是一个可复算的合法局部优化例子。成本下降不能替代功能等价验证；顺序与当前覆盖会影响后续操作。')

def front05():
    c=Canvas('front-m05-factor','m05','因式分解：相同功能可以有不同门网络','比较 f = ab + ac 与 f = a(b + c)；只统计二输入 AND/OR 门，不计导线与扇出缓冲。')
    c.text(230,130,'基线：3 个门',28,bold=True,anchor='middle');c.text(890,130,'分解：2 个门',28,bold=True,anchor='middle')
    for y in [230,420]:c.gate(250,y,'AND',90,80)
    c.gate(470,325,'OR',90,80)
    c.text(45,230,'a',24);c.text(45,285,'b',24);c.text(45,475,'c',24)
    c.line([(75,245),(150,245),(150,250),(250,250)],arrow=True)
    c.circle(150,245,5,fill=INK);c.line([(150,245),(150,440),(250,440)],arrow=True)
    c.line([(75,300),(250,300)],arrow=True);c.line([(75,490),(250,490)],arrow=True)
    c.line([(340,270),(410,270),(410,345),(470,345)],arrow=True)
    c.line([(340,460),(410,460),(410,385),(470,385)],arrow=True)
    c.line([(560,365),(600,365)],arrow=True);c.text(575,325,'f',24,bold=True)
    c.gate(800,340,'OR',95,80);c.gate(1020,250,'AND',100,90)
    c.text(660,240,'a',24);c.text(660,345,'b',24);c.text(660,395,'c',24)
    c.line([(690,260),(1020,270)],arrow=True)
    c.line([(690,360),(800,360)],arrow=True);c.line([(690,410),(800,410)],arrow=True)
    c.line([(895,380),(955,380),(955,320),(1020,320)],arrow=True)
    c.line([(1120,295),(1170,295)],arrow=True);c.text(1135,250,'f',24,bold=True)
    c.box(70,565,1060,150,'省门数 ≠ 自动提高所有性能',['两种网络的最长逻辑深度都是 2 级。分解后 a→f 为 1 级，b/c→f 仍为 2 级。','面积与时序还取决于标准单元、负载、扇出、布局布线。统一这些条件后才能作真实性能比较。','代数核验：分配律 a(b+c)=ab+ac；再对 8 行输入复算可独立验证。'])
    c.save('左图两个AND分别算ab和ac再进OR，共3门。右图OR先算b+c再与a进入AND，共2门。两者最长路径均为2级。','门数是明确约定下的结构成本。该图不声称真实面积、功耗或延迟按门数同比缩减。')
    c=Canvas('front-m05-decomposition','m05','函数分解：先把相同余函数分成一类','f = ab + ac；绑定变量 X=(b,c)，自由变量 Y=a。不是仅按相同输出值分组。')
    c.table(100,155,['固定 bc','00','01','10','11'],[['剩余 a 函数','0','a','a','a'],['所属类别','类0','类1','类1','类1'],['编码 z','0','1','1','1']],[240,190,190,190,190],rh=65,size=25)
    c.box(80,470,470,170,'两种不同的余函数',['类0：恒为 0。类1：返回 a。','所以 μ=2，至少需要 1 个编码位。','取 z=b+c，刚好区分类0/类1。'])
    c.box(660,470,460,170,'再组合：f = a·z',['z=0 时，f=0。','z=1 时，f=a。','两类均匹配表，因此分解成立。'])
    c.line([(550,550),(660,550)],arrow=True)
    c.text(80,690,'边界：若余函数有 3 类，需要至少 2 位；不同分区可能改变类数与实现成本。',24,bold=True)
    c.save('固定bc为00、01、10、11后，关于a的余函数依次为0、a、a、a；分为两类，编码z取0、1、1、1，即z=b+c，最后f=az。','余函数比较的是整个剩余函数，不是选一个输入点比较值；μ=2给出一位编码下界。')

def bdd_build(order):
    unique={};nodes={}
    def rec(k,a):
        if k==4:return int(a['a']==a['c'] and a['b']==a['d'])
        v=order[k];lo=rec(k+1,{**a,v:0});hi=rec(k+1,{**a,v:1})
        if lo==hi:return lo
        key=(v,lo,hi)
        if key not in unique:unique[key]=len(unique)+2;nodes[unique[key]]={'var':v,'low':lo,'high':hi,'depth':k}
        return unique[key]
    return rec(0,{}),nodes

def front06():
    c=Canvas('front-m06-bdd','m06','ROBDD：变的是共享结构，不是函数','f = XNOR(a,c) AND XNOR(b,d)：两对比特分别相等；无 complemented edges。',1400,940)
    for panel,order in enumerate(['abcd','acbd']):
        offset=panel*700;root,nodes=bdd_build(order);pos={0:(offset+60,760),1:(offset+640,760)}
        for depth in range(4):
            ns=[n for n in nodes if nodes[n]['depth']==depth];ns.sort()
            for j,n in enumerate(ns):pos[n]=(offset+100+(j+1)*500/(len(ns)+1),235+depth*125)
        c.text(offset+350,125,'顺序 '+ ' → '.join(order),27,bold=True,anchor='middle')
        c.text(offset+350,170,f'{len(nodes)} 个非终端节点',25,fill=TEAL,bold=True,anchor='middle')
        # all edges first; skipped-level terminal edges route through side rails to avoid crossing labels.
        for n,d in nodes.items():
            x,y=pos[n]
            for value,key,col in [(0,'low',BLUE),(1,'high',ORANGE)]:
                target=d[key];xx,yy=pos[target];sx=x+(-12 if value==0 else 12)
                if target<=1:
                    rail=offset+(32+6*n if target==0 else 668-6*n)
                    pts=[(sx,y+24),(sx,y+42),(rail,y+58),(rail,yy-40),(xx,yy-24)]
                else:pts=[(sx,y+24),(xx,yy-27)]
                c.line(pts,col,2,arrow=True,dash=value==0)
        for n,d in nodes.items():
            x,y=pos[n];c.circle(x,y,27,fill=PAPER,stroke=TEAL,lw=3);c.text(x,y-17,d['var'],26,bold=True,anchor='middle')
        for v in [0,1]:
            x,y=pos[v];c.rect(x-25,y-25,50,50,fill=LIGHT,stroke=INK,r=4);c.text(x,y-18,v,28,bold=True,anchor='middle')
    c.line([(700,115),(700,810)],GRID,1)
    c.text(65,810,'蓝色虚线 = 0 分支；橙色实线 = 1 分支。非终端只数圆圈，两个方框不计入 9 / 6。',23,bold=True)
    c.text(65,850,'验证同一输入：a=b=c=d=1，两图均沿相应 1 分支到终端 1；abcd=0101 也得到 1。',22)
    c.save('左图变量顺序abcd有9个非终端节点，右图acbd有6个。虚线蓝边为low0，实线橙边为high1，终端0和1用方框表示。','这是完全构造并约简的两张ROBDD；改变变量序不改布尔函数，但会改变节点共享和规模。图中每个节点的0/1边都有独立标识。')

def front07():
    c=Canvas('front-m07-fsm','m07','重叠检测 101：状态记录“有用的后缀”','Mealy 机；边标签是 输入 / 输出；每次消费一个输入比特。复位到 S0。')
    pos={'S0':(230,300),'S1':(600,300),'S2':(960,300)}
    c.line([(60,300),(160,300)],arrow=True);c.text(60,255,'复位',23)
    c.line([(300,280),(530,280)],arrow=True);c.text(415,235,'1 / 0',25,anchor='middle')
    c.line([(670,280),(890,280)],arrow=True);c.text(780,235,'0 / 0',25,anchor='middle')
    c.line([(920,355),(920,445),(640,445),(640,365)],GREEN,3,arrow=True);c.text(780,402,'1 / 1：识别到 101',24,fill=GREEN,anchor='middle')
    c.line([(1000,355),(1000,510),(230,510),(230,370)],BLUE,3,arrow=True);c.text(510,472,'0 / 0：100 不保留有效前缀',23,fill=BLUE,anchor='middle')
    for key,label in [('S0','无前缀'),('S1','已见 1'),('S2','已见 10')]:
        x,y=pos[key];c.circle(x,y,70,fill=LIGHT,stroke=TEAL,lw=3);c.text(x,y-35,key,27,bold=True,anchor='middle');c.text(x,y+8,label,20,anchor='middle')
    for x,label in [(230,'0 / 0'),(600,'1 / 0')]:
        c.line([(x-35,240),(x-35,160),(x+35,160),(x+35,240)],INK,3,arrow=True);c.text(x,120,label,24,anchor='middle')
    c.table(80,575,['输入序列','1','0','1','0','1'],[['本拍前状态','S0','S1','S2','S1','S2'],['输出','0','0','1','0','1'],['本拍后状态','S1','S2','S1','S2','S1']],[240]+[160]*5,rh=42,size=22)
    c.save('三个状态S0、S1、S2表示无前缀、见1、见10。S2收到1输出1并回到S1，所以输入10101可以识别重叠的两个101，输出00101。','识别成功后保留末尾1作为下一次匹配的前缀；若回到S0就会漏掉重叠检测。此图的输出在边上，不是Moore状态输出。')

def back_specs():
    return {x['id']:x for x in json.loads((ROOT/'content/figure-specs-back.json').read_text(encoding='utf-8'))}

def back08():
    c=Canvas('back-m08-pulse','m08','同一个短脉冲：transport 保留，简化 inertial 抑制','初始 I=O=0；输入 1 ns 上升、3 ns 下降；脉宽 w=2 ns，门延迟 d=3 ns。')
    tx=lambda t:260+105*t
    for t in range(9):
        c.line([(tx(t),175),(tx(t),610)],GRID,1,dash=True)
        c.text(tx(t),625,str(t),23,anchor='middle')
    for name,y,edges,col in [('输入 I',200,[(0,0),(1,1),(3,0)],INK),('transport',360,[(0,0),(4,1),(6,0)],BLUE),('inertial',520,[(0,0)],ORANGE)]:
        c.text(45,y+15,name,27,bold=True,fill=col)
        c.text(225,y-6,'1',18,fill=MUTED);c.text(225,y+60,'0',18,fill=MUTED)
        pts=[];last=0
        for t,v in edges:
            pts += [(tx(t),y+70*(1-last)),(tx(t),y+70*(1-v))];last=v
        pts.append((tx(8),y+70*(1-last)));c.line(pts,col,4)
    c.line([(tx(1),155),(tx(4),155)],BLUE,3,arrow=True);c.text((tx(1)+tx(4))/2,115,'对应上升沿平移 3 ns',22,fill=BLUE,anchor='middle')
    c.text(550,290,'宽度仍为 2 ns',22,fill=BLUE);c.text(640,465,'3 ns 撤销尚未执行的 4 ns→1',22,fill=ORANGE)
    c.text(1140,625,'ns',23)
    c.box(60,680,1080,70,'比较：w < d 被抑制；此教学模型保留 w = d 的脉冲',color=TEAL)
    c.save('同一横轴0到8纳秒：输入在1到3纳秒为1，transport输出在4到6纳秒为1，简化inertial输出保持0。','单门、单驱动、单个孤立脉冲、二值模型；不是完整VHDL projected waveform规则或模拟电压预测。')
    d=back_specs()['back-m08-queue']['data']
    c=Canvas('back-m08-queue','m08','事件账本：安排未来事务 ≠ 输出现在改变','表内状态为处理该时刻事件之后；“4→1”表示在 4 ns 执行赋值 1。')
    c.table(45,155,['t / ns','输入变化','transport 队列','输出','inertial 队列','输出'],d['rows'],[90,160,270,80,370,80],rh=65,size=21)
    c.box(60,585,510,130,'1 ns：排队，不是立刻输出',['两种模型都只安排未来 4→1。','当前输出仍为 0，队列占用为 1。'])
    c.box(630,585,510,130,'3 ns：两种队列开始分叉',['transport 留 4→1，再加 6→0。','inertial 撤销上升，同值 0 事务省略。'])
    c.save('队列表列出0、1、3、4、6纳秒处理后状态：transport在3纳秒队列为4→1和6→0，inertial则撤销4→1。','队列是模拟器的因果记录，不是电路里实际存在的一条队列。只列影响输出变化的有效事务。')

def back09():
    d=back_specs()['back-m09-delta']['data']
    c=Canvas('back-m09-delta','m09','signal 与 variable：同一段顺序代码的两种更新','同一时钟进程；sa/sb/q/r 是 signal；va/vb 是持久局部 variable；无 after 延迟。')
    c.box(40,150,375,380,'每个上升沿执行')
    for i,s in enumerate(d['code']):c.text(80,215+45*i,s,27,bold=True,fill=BLUE if '<=' in s else ORANGE)
    rows=[]
    for name,key in [('第1沿之前','initial'),('进程刚执行完','afterProcess'),('随后 delta 更新','afterDelta'),('第2沿及其更新后','afterSecondEdgeAndDelta')]:rows.append([name]+[d[key][k] for k in ['sa','sb','va','vb','q','r']])
    c.table(470,170,['阶段','sa','sb','va','vb','q','r'],rows,[235]+[73]*6,rh=65,size=23,colors={1:'#fff2df',2:'#e3f5ed'})
    c.text(470,535,'第1沿的未来 signal 事务：sa←1，sb←0，q←0，r←1',21,fill=BLUE,bold=True)
    c.box(55,600,1090,130,'为什么 q=0，而 r=1？',['q<=sa 读取当前 sa=0；sa<=sb 尚未生效。r<=va 读取立即更新后的 va=1。','signal 交换 sa/sb 成功；变量依次覆盖后 va=vb=1。delta 是同一物理时刻的更新轮次，不是 1 ns。'])
    c.save('左侧六行代码sa<=sb、sb<=sa、va:=vb、vb:=va、q<=sa、r<=va。右表显示进程后变量变11而信号保持01，delta后信号变10，q0r1。','读出右值的时机与写入生效的时机必须分开记录。图中变量初始化一次并跨时钟沿保持，不在每次调用时重置。')

def small_circuit(c,x,y,fault=False,labels=True):
    # Panel span about 520 px. Inputs and output labels remain outside wire paths.
    col=RED if fault else TEAL
    c.gate(x+130,y+65,'AND',95,80);c.gate(x+360,y+130,'OR',90,80)
    c.text(x,y+55,'a = 1',23);c.text(x,y+110,'b = 1',23);c.text(x,y+240,'c = 0',23)
    c.line([(x+75,y+85),(x+130,y+85)],arrow=True);c.line([(x+75,y+130),(x+130,y+130)],arrow=True)
    c.line([(x+225,y+105),(x+300,y+105),(x+300,y+150),(x+360,y+150)],col,3,arrow=True)
    c.text(x+242,y+58,'n = '+('0' if fault else '1'),23,fill=col,bold=True)
    if fault:c.circle(x+275,y+105,8,fill=RED,stroke=RED);c.text(x+235,y+5,'n/0 强制为0',21,fill=RED,bold=True)
    c.line([(x+75,y+258),(x+300,y+258),(x+300,y+190),(x+360,y+190)],arrow=True)
    c.line([(x+450,y+170),(x+520,y+170)],col,3,arrow=True)
    c.text(x+440,y+95,'y = '+('0' if fault else '1'),23,fill=col,bold=True)

def back10():
    c=Canvas('back-m10-fault','m10','一个测试向量必须同时做到：激活故障 ＋ 传播差异','网表 n=a AND b，y=n OR c；故障 n/0 意味着内部节点 n 永远被强制为 0。')
    c.text(285,130,'正常电路：abc = 110',27,fill=TEAL,bold=True,anchor='middle')
    c.text(885,130,'故障电路：abc = 110',27,fill=RED,bold=True,anchor='middle')
    small_circuit(c,40,190);small_circuit(c,640,190,True)
    c.table(85,550,['输入 abc','正常 n / y','故障 n / y','是否检测','原因'],[['110','1 / 1','0 / 0','是','激活，并传到输出'],['111','1 / 1','0 / 1','否','c=1 掩盖 n 差异'],['100','0 / 0','0 / 0','否','n 本来就是 0']],[160,200,200,150,320],rh=49,size=23,colors={0:'#e3f5ed'})
    c.save('左右并排的同一AND-OR电路输入110，正常n1y1，n/0故障电路n0y0。对比111仅激活却被c1掩盖，100连激活也没有。','观察点只有y。只有正常与故障y不同，才能说此向量检测该单stuck-at故障。')

def back11():
    c=Canvas('back-m11-dpath','m11','D 算法手算：先放差异，再把它送到输出','D = 正常 1 / 故障 0；X = 尚未决定。目标故障 n/0，网表 n=ab，y=n+c。')
    c.gate(440,260,'AND',115,95);c.gate(800,350,'OR',115,95)
    c.text(100,250,'a：X → 1',28,bold=True);c.text(100,325,'b：X → 1',28,bold=True)
    c.line([(260,285),(440,285)],arrow=True);c.line([(260,335),(440,335)],arrow=True)
    c.line([(555,307),(700,307),(700,375),(800,375)],RED,4,arrow=True)
    c.text(600,245,'n = D',30,fill=RED,bold=True)
    c.text(425,485,'c：X → 0',28,bold=True);c.line([(610,505),(720,505),(720,425),(800,425)],arrow=True)
    c.line([(915,397),(1110,397)],RED,4,arrow=True);c.text(990,340,'y = D',30,fill=RED,bold=True)
    c.box(45,140,315,70,'③ 反推：AND 要输出1',color=BLUE)
    c.box(440,140,315,70,'① 激活：正常 n 必须1',color=RED)
    c.box(825,140,330,70,'② 传播：OR 旁路置0',color=TEAL)
    c.table(70,585,['阶段','a','b','c','n','y'],[['激活目标','X','X','X','D','X'],['传播到 y','X','X','0','D','D'],['反推完成','1','1','0','D','D']],[330]+[145]*5,rh=42,size=24)
    c.save('n处放D代表正常1故障0，OR要传播D则旁路c必须0，AND正常端要n1则a和b都必须1；最终向量110使y=D。','这是单目标的成功手算路径；复杂电路必须继续检查全局蕴含与冲突，某条路径失败不代表故障不可测。')

def back12():
    d=back_specs()['back-m12-matrix']['data']
    c=Canvas('back-m12-matrix','m12','完整故障矩阵：行是输入，列是候选单故障','n=ab，y=n+c；每次只注入一个故障，只观察y。1 = 正常输出与故障输出不同。',1400,880)
    rows=[]
    for r in d['rows']:rows.append([r['vector'],r['n'],r['goodY']]+['1' if v else '·' for v in r['detected']])
    c.table(50,155,['abc','n','y']+d['faults'],rows,[120,65,65]+[105]*10,rh=49,size=24,colors={1:'#e3f5ed',2:'#e3f5ed',4:'#e3f5ed',6:'#e3f5ed'})
    c.text(65,635,'一组最小测试集：{001, 010, 100, 110}，覆盖 10 / 10 个原始故障。',27,fill=GREEN,bold=True)
    c.lines(65,685,['至少 4 条的证据：a/1 只能由010检测；b/1 只能由100检测；n/0 只能由110检测。','这三条都不检测 c/0，故还须 001、011、101 中至少一条。图中绿色选 001。','“·”表示 0；颜色仅辅助阅读。不能把某一条向量的覆盖率当成整组覆盖率。'],23)
    c.save('8行输入000至111、10列故障a/0、a/1、b/0、b/1、c/0、c/1、n/0、n/1、y/0、y/1组成完整检测矩阵。突出001、010、100、110四行。','每个格子由独立良好/故障电路计算。必选010、100、110后，还需一条c/0检测向量，证明最小集大小为4。')

def back13():
    d=back_specs()['back-m13-lfsr']['data']
    c=Canvas('back-m13-lfsr','m13','LFSR：明确位顺序，再数第一次重复','4 位右移，状态写成 s3 s2 s1 s0；反馈 f = s0 XOR s1；next = [f, s3, s2, s1]。',1400,980)
    for i,lab in enumerate(['s3','s2','s1','s0']):
        x=275+i*230;c.box(x,190,130,100,lab,['触发器'])
        if i<3:c.line([(x+130,240),(x+230,240)],TEAL,3,arrow=True)
    c.line([(1095,240),(1270,240)],arrow=True);c.text(1170,190,'输出旧 s0',23)
    c.gate(700,370,'XOR',120,90)
    c.line([(800,290),(800,340),(780,340),(780,370)],BLUE,3,arrow=True);c.circle(800,290,5,fill=BLUE,stroke=BLUE)
    c.line([(1030,290),(1030,420),(820,420)],BLUE,3,arrow=True);c.circle(1030,290,5,fill=BLUE,stroke=BLUE)
    c.line([(700,415),(180,415),(180,240),(275,240)],ORANGE,3,arrow=True)
    c.text(300,370,'反馈 f；送入新的 s3',24,fill=ORANGE,bold=True)
    c.text(70,500,'从 0001 开始：完整 15 态；最后箭头回到 0001',27,bold=True)
    states=[r['bits'] for r in d['trace']]+['0001']
    for row in range(2):
        for j in range(8):
            idx=row*8+j;x=60+j*165;y=565+row*115
            c.rect(x,y,130,65,fill='#e3f5ed' if idx in (0,15) else LIGHT,stroke=TEAL,r=7)
            c.text(x+65,y+16,states[idx],25,bold=True,anchor='middle')
            if j<7:c.line([(x+130,y+32),(x+160,y+32)],arrow=True)
        if row==0:c.line([(1345,597),(1370,597),(1370,655),(40,655),(40,712),(60,712)],INK,2,arrow=True)
    c.box(70,795,1260,120,'核验与边界',['0001：s0 XOR s1 = 1，右移后成为 1000。15 个非零状态各出现一次；0000 则一直是0000。','mask=0011 只指抽头位置。换移位方向或位编号后不能照抄这个序列。'])
    c.save('四个触发器从s3向s0右移，s0和s1异或反馈到s3。完整非零序列0001、1000、0100、0010、1001、1100、0110、1011、0101、1010、1101、1110、1111、0111、0011后回0001。','所有更新同时使用旧状态。周期15只对应此明确递推与非零种子；全零种子锁在零态。')
    c=Canvas('back-m13-scan','m13','Scan 时间账本：边卸旧响应，边装新向量','4 个扫描触发器，3 组测试，每组 1 拍 capture；共用一条链，不计模式切换开销。',1400,960)
    c.text(50,130,'一条链同时搬两份信息',26,bold=True)
    for i,lab in enumerate(['Q3','Q2','Q1','Q0']):
        x=300+i*220;c.box(x,180,110,85,lab)
        if i<3:c.line([(x+110,223),(x+220,223)],TEAL,3,arrow=True)
    c.line([(100,223),(300,223)],TEAL,3,arrow=True);c.text(90,175,'scan_in',24)
    c.line([(1070,223),(1290,223)],TEAL,3,arrow=True);c.text(1150,175,'旧 Q0 输出',24)
    c.text(70,320,'时钟拍',23,bold=True)
    start=180;cw=60
    for t in range(1,20):
        x=start+(t-1)*cw;c.rect(x,365,cw,60,fill='#fff1dd' if t in [5,10,15] else '#def1e8',stroke=PAPER)
        c.text(x+cw/2,330,t,21,anchor='middle');c.text(x+cw/2,381,'C' if t in [5,10,15] else 'S',24,bold=True,anchor='middle')
    c.text(70,450,'S = shift：移位/采样；C = capture：捕获响应。每个小格都占 1 拍。',24,bold=True)
    rows=[['1–4','装入 P1=1010','忽略初态输出'],['5','capture：R1=0101','教学功能 Q←NOT Q'],['6–9','装入 P2=0011','同时卸 R1=0101'],['10','capture：R2=1100','教学功能 Q←NOT Q'],['11–14','装入 P3=1110','同时卸 R2=1100'],['15','capture：R3=0001','教学功能 Q←NOT Q'],['16–19','装入填充0','最后卸 R3=0001']]
    c.table(75,505,['区段 / 拍','输入或捕获','同时输出或说明'],rows,[200,500,550],rh=38,size=22)
    c.text(75,835,'重叠：N(P+1)+P = 4×4+3 = 19 拍；不重叠：(2N+1)P = 9×3 = 27 拍。',27,fill=TEAL,bold=True)
    c.text(75,880,'装 P1=1010 时串行输入顺序是 0、1、0、1；响应文字按 Q3Q2Q1Q0 写，线上旧 Q0 先出。',22)
    c.save('扫描链Q3到Q0右移，共19拍：1至4装P1，5捕获R1，6至9出R1入P2，10捕R2，11至14出R2入P3，15捕R3，16至19末次卸R3。','capture的取反功能仅为独立教学例，与LFSR递推无关；N(P+1)+P假设相邻组允许同时移出旧响应和移入新测试。')

def write_manifest():
    (ROOT/'content/figures.json').write_text(json.dumps(MANIFEST,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'qa').mkdir(exist_ok=True)
    (ROOT/'qa/figures-check.json').write_text(json.dumps({'status':'in-progress','figures':len(MANIFEST),'renderChecks':CHECKS,'method':'同一绘图命令生成SVG与2倍分辨率PNG；Microsoft YaHei字体；原创机制图，数值分别重算。'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def verify_numbers():
    """Independent small exhaustive checks; fail generation when teaching data drifts."""
    done={}
    fs={x['id']:x for x in json.loads((ROOT/'content/figure-specs-front.json').read_text(encoding='utf-8'))}
    bs=back_specs()
    good=lambda a,b,c:(a and b) or c
    truth=[[v,(v>>2)&1,(v>>1)&1,v&1,((v>>2)&1)&((v>>1)&1),int(good((v>>2)&1,(v>>1)&1,v&1))] for v in range(8)]
    assert truth==fs['front-m01-flow']['rows'];done['front-m01-flow']='8行真值与n中间量独立穷举，与spec逐格一致。'
    done['front-m01-ychart']='人工对照L25 PDF9–10：system/algorithm/RT/logic/circuit由外至内，三域与层级独立。'
    for a,b,cin in itertools.product([0,1],repeat=3):
        p=a^b;s=p^cin;ca=(a&b)|(p&cin);cb=(a&b)|(a&cin)|(b&cin)
        assert a+b+cin==s+2*ca and ca==cb
    done['front-m01-adder']='8输入同时核验整数和与两carry表达；显式固定XOR2/AND1/OR1及三输入OR，路径4与2。'
    assert [truth[v][5] for row in fs['front-m02-kmap']['indices'] for v in row]==sum(fs['front-m02-kmap']['values'],[])
    done['front-m02-kmap']='Gray列、minterm编号、全部值与两分组的固定变量独立核验。'
    for a,b,c in itertools.product([0,1],repeat=3):assert good(a,b,c)==((not a) and c or a and (b or c))
    done['front-m02-cofactor']='8行验证f0=c、f1=b+c及带选择条件的Shannon等式；010反例成立。'
    match=lambda p,v:all(x=='-' or x==y for x,y in zip(p,f'{v:03b}'))
    on={0,1,2,5,6,7};allp=[]
    for tup in itertools.product('01-',repeat=3):
        p=''.join(tup);covered={v for v in range(8) if match(p,v)}
        if not covered<=on:continue
        if all(not {v for v in range(8) if match(p[:i]+'-'+p[i+1:],v)}<=on for i,x in enumerate(p) if x!='-'):allp.append(p)
    primes=fs['front-m03-quine']['primes'];assert set(allp)=={p['cube'] for p in primes}
    for p in primes:assert sorted(v for v in on if match(p['cube'],v))==p['minterms']
    done['front-m03-quine']='独立枚举27个cube，全部合法极大cube恰为P..U六项，无2-cube。'
    covers=[]
    for combo in itertools.combinations(primes,3):
        if set().union(*(set(p['minterms']) for p in combo))==on:covers.append(''.join(p['id'] for p in combo))
    assert set(covers)=={'PST','QRU'};done['front-m03-cover']='覆盖矩阵逐格核验，独立枚举三项组合仅PST/QRU；下界3项。'
    patterns=[['111','110','011'],['11-','110','011'],['11-','011'],['11-','-11']]
    assert [sum(len(p.replace('-','')) for p in ps) for ps in patterns]==[9,8,5,4]
    assert all({v for v in range(8) if any(match(p,v) for p in ps)}=={3,6,7} for ps in patterns)
    done['front-m04-trajectory']='每阶段8行穷举同ON={3,6,7}；literal9/8/5/4，路径与front specs一致。'
    for a,b,c in itertools.product([0,1],repeat=3):assert ((a&b)|(a&c))==(a&(b|c))
    done['front-m05-factor']='8行等价验证，3门/2门及最长2级按真实导线计数。'
    done['front-m05-decomposition']='四个bc余函数逐个枚举a=0/1，只有00对应0，其余为a；两类一位。'
    for order,count in [('abcd',9),('acbd',6)]:
        root,nodes=bdd_build(order);assert len(nodes)==count
        for a,b,c,d in itertools.product([0,1],repeat=4):
            assignment=dict(zip('abcd',[a,b,c,d]));u=root
            while u>1:u=nodes[u]['high' if assignment[nodes[u]['var']] else 'low']
            assert u==int(a==c and b==d)
    done['front-m06-bdd']='独立构造无补边ROBDD，16输入各在两序下核验，非终端9/6。'
    trans={('S0',0):('S0',0),('S0',1):('S1',0),('S1',0):('S2',0),('S1',1):('S1',0),('S2',0):('S0',0),('S2',1):('S1',1)}
    state='S0';trace=[]
    for i,b in enumerate([1,0,1,0,1],1):n,o=trans[state,b];trace.append([i,b,state,o,n]);state=n
    assert trace==fs['front-m07-fsm']['trace'];done['front-m07-fsm']='逐拍重算10101→00101，六条边每状态两个输入完备，匹配后回S1。'
    assert bs['back-m08-pulse']['data']['transport']==[[0,0],[4,1],[6,0]]
    assert 3-1<3;done['back-m08-pulse']='手算沿时间1+3=4、3+3=6，w2<d3过滤；图横轴统一ns。'
    done['back-m08-queue']='按每次输入/输出事件逐项确认队列只包含已生成尚未执行事务；同值0事务明确省略。'
    sig={'sa':0,'sb':1,'q':0,'r':0};var={'va':0,'vb':1}
    for key in ['afterDelta','afterSecondEdgeAndDelta']:
        pending={'sa':sig['sb'],'sb':sig['sa']};var['va']=var['vb'];var['vb']=var['va'];pending['q']=sig['sa'];pending['r']=var['va'];sig.update(pending)
        assert {**sig,**var}==bs['back-m09-delta']['data'][key]
    done['back-m09-delta']='独立按顺序代码求值，signal批量提交，variable立即写；两沿所有6个值与spec一致。'
    def run(v,fault=None):
        a,b,c=map(int,f'{v:03b}');state={'a':a,'b':b,'c':c}
        if fault and fault[0] in state:state[fault[0]]=fault[1]
        state['n']=state['a']&state['b']
        if fault and fault[0]=='n':state['n']=fault[1]
        state['y']=state['n']|state['c']
        if fault and fault[0]=='y':state['y']=fault[1]
        return state
    for r in bs['back-m10-fault']['data']['cases']:
        v=int(r['vector'],2);g=run(v);f=run(v,('n',0));assert (g['y']!=f['y'])==r['detected']
    done['back-m10-fault']='110、111、100的正常/故障n,y四值分别重算，区分传播与激活失败。'
    assert run(6)['n']==1 and run(6)['y']==1 and run(6,('n',0))['y']==0
    done['back-m11-dpath']='110独立重算满足n与y均为(1,0)差异；c0是OR旁路非控制值。'
    faults=[(s,v) for s in ['a','b','c','n','y'] for v in [0,1]];matrix=[[int(run(v)['y']!=run(v,f)['y']) for f in faults] for v in range(8)]
    assert matrix==[r['detected'] for r in bs['back-m12-matrix']['data']['rows']]
    for k in range(1,5):
        sets=[combo for combo in itertools.combinations(range(8),k) if all(any(matrix[v][j] for v in combo) for j in range(10))]
        if sets:break
    assert k==4 and set(sets)=={(1,2,4,6),(2,3,4,6),(2,4,5,6)}
    done['back-m12-matrix']='独立注入80个故障情况与矩阵逐格一致；穷举输入子集最小4条及全部3组解。'
    state=[0,0,0,1];seq=[]
    while state not in seq:seq.append(state[:]);state=[state[2]^state[3]]+state[:3]
    assert len(seq)==15 and state==[0,0,0,1]
    assert [''.join(map(str,b)) for b in seq]==[r['bits'] for r in bs['back-m13-lfsr']['data']['trace']]
    done['back-m13-lfsr']='独立4元素bit数组右移与反馈，完整15态序列逐项匹配；零态固定点。'
    q=[0,0,0,0];cycles=0;response=None
    for pat in ['1010','0011','1110']:
        unloaded=[]
        for bit in reversed(pat):unloaded.append(q[-1]);q=[int(bit)]+q[:-1];cycles+=1
        if response is not None:assert unloaded==list(reversed(response))
        assert ''.join(map(str,q))==pat
        q=[1-b for b in q];response=q[:];cycles+=1
    unloaded=[]
    for i in range(4):unloaded.append(q[-1]);q=[0]+q[:-1];cycles+=1
    assert cycles==19 and unloaded==list(reversed(response))
    done['back-m13-scan']='按4位链实际移入/移出并capture取反，三个图样及响应逐段匹配，共19拍；不重叠27拍。'
    assert set(done)=={f['id'] for f in MANIFEST}
    return done

if __name__=='__main__':
    front01()
    front01_extra()
    front02()
    front03()
    front04()
    front05()
    front06()
    front07()
    back08()
    back09()
    back10()
    back11()
    back12()
    back13()
    write_manifest()
    numeric=verify_numbers()
    qpath=ROOT/'qa/figures-check.json';q=json.loads(qpath.read_text(encoding='utf-8'));q['numericalChecks']=numeric;q['numericalStatus']='pass';qpath.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Generated {len(MANIFEST)} figures; {len(CHECKS)} layout warnings')
