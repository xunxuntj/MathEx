"""Build the submission PDF from the Markdown mother document."""
from __future__ import annotations
import html, re
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph,
                               Spacer, Table, TableStyle, PageBreak)

BASE=next(Path('.').glob('*/06-研究方案与研究结果.md')).parent
SRC=BASE/'06-研究方案与研究结果.md'; OUT=BASE/'06-研究方案与研究结果.pdf'
pdfmetrics.registerFont(TTFont('CN','C:/Windows/Fonts/simhei.ttf'))

def clean(s):
    s=s.replace('\\(','').replace('\\)','')
    for a,b in {'\\binom n3':'C(n,3)','\\binom r3':'C(r,3)','\\binom s2':'C(s,2)',
                '\\binom r2':'C(r,2)','\\binom n2':'C(n,2)','\\binom{t_v}{2}':'C(t_v,2)',
                '\\binom{d}{2}':'C(d,2)','\\binom{r}{3}':'C(r,3)','\\binom{r}{2}':'C(r,2)',
                '\\binom{s}{2}':'C(s,2)'}.items(): s=s.replace(a,b)
    replacements={'\\ge':'≥','\\le':'≤','\\cup':'∪','\\max':'max','\\min':'min',
                  '\\quad':'  ','\\tag{1}':'(1)','\\tag{2}':'(2)','\\tag{3}':'(3)','\\tag{4}':'(4)',
                  '\\left':'','\\right':'','\\lceil':'⌈','\\rceil':'⌉','\\sum_v':'Σv',
                  '\\deg':'deg','\\delta':'δ','\\Delta':'Δ'}
    for a,b in replacements.items(): s=s.replace(a,b)
    s=re.sub(r'\\binom\s*\{?([^\s{}]+)\}?\s*\{?([^\s{}]+)\}?',r'C(\1,\2)',s)
    s=re.sub(r'\\frac\{([^{}]+)\}\{([^{}]+)\}',r'(\1)/(\2)',s)
    s=re.sub(r'\\text\{([^{}]+)\}',r'\1',s)
    s=s.replace('\\left\\ceil','⌈').replace('\\right\\rceil','⌉')
    s=s.replace('\\{','{').replace('\\}','}').replace('\\,',' ').replace('\\!','')
    s=html.escape(s.strip())
    s=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
    s=re.sub(r'`(.+?)`',r'<font name="Courier">\1</font>',s)
    return s

styles=getSampleStyleSheet()
body=ParagraphStyle('body',fontName='CN',fontSize=9.4,leading=15,spaceAfter=4,textColor=colors.HexColor('#172033'))
h1=ParagraphStyle('h1',parent=body,fontSize=19,leading=25,alignment=TA_CENTER,spaceAfter=16,textColor=colors.HexColor('#123B5D'))
h2=ParagraphStyle('h2',parent=body,fontSize=14,leading=20,spaceBefore=10,spaceAfter=6,textColor=colors.HexColor('#146C7E'))
h3=ParagraphStyle('h3',parent=body,fontSize=11.5,leading=17,spaceBefore=7,spaceAfter=4,textColor=colors.HexColor('#235789'))
eq=ParagraphStyle('eq',parent=body,alignment=TA_CENTER,fontSize=9.2,leading=14,backColor=colors.HexColor('#F3F7FA'),borderPadding=5,spaceBefore=4,spaceAfter=6)
bullet=ParagraphStyle('bullet',parent=body,leftIndent=14,firstLineIndent=-8)
small=ParagraphStyle('small',parent=body,fontSize=7.5,leading=10)

class Doc(BaseDocTemplate):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        fr=Frame(self.leftMargin,self.bottomMargin,self.width,self.height,id='main')
        self.addPageTemplates(PageTemplate(id='p',frames=fr,onPage=self.header))
    def header(self,canv,doc):
        canv.saveState();canv.setFont('CN',7.5);canv.setFillColor(colors.HexColor('#5B6670'))
        canv.drawString(18*mm,12*mm,'第五届上海市中学数学学术展评活动 · 长期题二')
        canv.drawRightString(192*mm,12*mm,f'{doc.page}')
        canv.restoreState()

def parse(lines):
    story=[]; i=0; in_eq=False; eqbuf=[]
    while i<len(lines):
        raw=lines[i].rstrip(); s=raw.strip()
        if s=='\\[': in_eq=True;eqbuf=[];i+=1;continue
        if in_eq:
            if s=='\\]':
                story.append(Paragraph(clean(' '.join(eqbuf)),eq));in_eq=False
            else:eqbuf.append(s)
            i+=1;continue
        if not s: story.append(Spacer(1,2));i+=1;continue
        if s.startswith('|') and i+1<len(lines) and re.match(r'^\|?\s*:?-+',lines[i+1].strip()):
            rows=[]; headers=[x.strip() for x in s.strip('|').split('|')];rows.append(headers);i+=2
            while i<len(lines) and lines[i].strip().startswith('|'):
                rows.append([x.strip() for x in lines[i].strip().strip('|').split('|')]);i+=1
            data=[[Paragraph(clean(x),small) for x in row] for row in rows]
            widths=[(174*mm)/len(headers)]*len(headers)
            t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
            t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'CN'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DDECF2')),('TEXTCOLOR',(0,0),(-1,0),colors.HexColor('#123B5D')),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#9FB6C1')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]))
            story.extend([t,Spacer(1,6)]);continue
        if s.startswith('# '):story.append(Paragraph(clean(s[2:]),h1))
        elif s.startswith('## '):story.append(Paragraph(clean(s[3:]),h2))
        elif s.startswith('### '):story.append(Paragraph(clean(s[4:]),h3))
        elif re.match(r'^[-*] ',s):story.append(Paragraph('- '+clean(s[2:]),bullet))
        elif re.match(r'^\d+\. ',s):story.append(Paragraph(clean(s),bullet))
        else:story.append(Paragraph(clean(s),body))
        i+=1
    return story

doc=Doc(str(OUT),pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=16*mm,bottomMargin=18*mm,title='长期题二研究方案与研究结果',author='娄山中学参赛团队')
doc.build(parse(SRC.read_text(encoding='utf-8').splitlines()))
print(OUT)
